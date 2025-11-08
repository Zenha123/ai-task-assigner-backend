import os
import json
import logging
from typing import Dict, Any, List
from django.conf import settings
from celery import shared_task
from .models import Task, Employee, AssignmentLog

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)


def get_llm():
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("⚠️ No OpenAI API key found; running in mock mode.")
        return None
    print(f"✅ Using OpenAI API key (starts with {api_key[:7]}...)")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)



# ---------- Pipeline Nodes ----------
#
import re

def task_parser_node(task: Task) -> Dict[str, Any]:
    """Extract candidate skills/keywords from the task title & description."""
    llm = get_llm()
    if not llm:
        # fallback if no key or offline
        keywords = (task.title + " " + task.description).lower().split()[:10]
        return {"keywords": keywords, "skills": [], "technical_tags": [], "effort_level": "medium"}

   
    prompt = PromptTemplate(
    input_variables=["title", "description"],
    template=(
        "You are a precise JSON generator. "
        "Given the task title and description, return only valid JSON with these fields:\n"
        "{{"
        "  \"keywords\": [list of important words], "
        "  \"skills\": [list of related technical skills], "
        "  \"technical_tags\": [list of tech/tools mentioned], "
        "  \"effort_level\": \"low\"|\"medium\"|\"high\""
        "}}\n"
        "Respond with ONLY JSON. No extra text, explanations, or code fences.\n\n"
        "Title: {title}\n"
        "Description: {description}"
    ),
)


    text = prompt.format(title=task.title, description=task.description)
    try:
        result = llm.invoke(text)
        print("🧩 Raw model output:", result.content)
        parsed = json.loads(result.content)
        logger.info(f"[TaskParser] Parsed: {parsed}")
        return parsed
    except Exception as e:
        logger.exception(f"Task parser failed: {e}")
        return {"keywords": [], "skills": [], "technical_tags": [], "effort_level": "medium"}


def role_matching_node(parsed: Dict[str, Any]) -> List[Employee]:
    """Find employees whose role/skills match parsed keywords."""
    skills = set([s.lower() for s in parsed.get("skills", [])])
    keywords = set([k.lower() for k in parsed.get("keywords", [])])

    candidates = []
    for emp in Employee.objects.all():
        emp_skills = set([s.lower() for s in emp.skills or []])
        text_block = f"{emp.role} {emp.responsibilities or ''}".lower()

        skill_match = len(emp_skills & skills)
        keyword_match = sum(1 for k in keywords if k in text_block)
        score = (skill_match * 2) + keyword_match
        if score > 0:
            candidates.append((emp, score))

    candidates.sort(key=lambda x: (-x[1], x[0].workload_score))
    logger.info(f"[RoleMatching] {len(candidates)} candidates found")
    return [c[0] for c in candidates]


def workload_analyzer_node(candidates: List[Employee]) -> List[Dict[str, Any]]:
    """Return candidates with workload-adjusted availability score."""
    adjusted = []
    for emp in candidates:
        availability = max(0.0, 1.0 - emp.workload_score)
        adjusted_score = round(availability * 0.6 + 0.4, 2)
        adjusted.append({"employee": emp, "adjusted_score": adjusted_score})
    adjusted.sort(key=lambda x: -x["adjusted_score"])
    logger.info("[WorkloadAnalyzer] Adjusted workload scores calculated.")
    return adjusted


def confidence_scorer_node(task: Task, candidate_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute a confidence score (0–1) for each candidate using LLM or heuristic fallback."""
    llm = get_llm()
    results = []

    for info in candidate_info:
        emp = info["employee"]

        if not llm:
            # fallback if no API key / offline mode
            conf = float(min(1.0, info["adjusted_score"]))
            reason = "Heuristic confidence (no LLM)."
        else:
            prompt = (
                f"You are an expert technical evaluator.\n"
                f"Task: {task.title}\n"
                f"Description: {task.description}\n"
                f"Candidate: {emp.name} ({emp.role})\n"
                f"Skills: {emp.skills}\nResponsibilities: {emp.responsibilities}\n"
                f"Workload Score: {emp.workload_score}\n\n"
                "Respond with a single JSON object in this format:\n"
                '{"confidence": 0.xx, "reason": "short reason"}'
            )
            try:
                result = llm.invoke(prompt)
                print("🧠 ConfidenceScorer raw output:", result.content)

                # --- Try normal JSON parsing first ---
                try:
                    parsed = json.loads(result.content)
                except Exception:
                    # --- If model returns text, extract JSON with regex fallback ---
                    import re
                    json_match = re.search(r'\{.*\}', result.content, re.S)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                    else:
                        parsed = {"confidence": 0.6, "reason": "LLM returned invalid or empty response"}

                conf = float(parsed.get("confidence", 0.6))
                reason = parsed.get("reason", "No reason provided")

            except Exception as e:
                logger.exception(f"[ConfidenceScorer] LLM failed: {e}")
                conf = info["adjusted_score"]
                reason = "Fallback heuristic (LLM failed)"

        results.append({
            "employee": emp,
            "confidence": round(conf, 2),
            "reason": reason
        })

    # Sort candidates by descending confidence
    results.sort(key=lambda x: -x["confidence"])
    logger.info(f"[ConfidenceScorer] Completed for {len(results)} candidates.")
    return results



def decision_node(task: Task, scored: List[Dict[str, Any]], threshold: float = 0.75):
    """Decide if we auto-assign or send for review."""
    if not scored:
        AssignmentLog.objects.create(task=task, reasoning_text="No candidates", confidence=0.0, decision_status="no_candidates")
        return {"decision": "no_candidates", "reason": "No matching candidates", "email_sent": False}

    top = scored[0]
    emp, conf, reason = top["employee"], top["confidence"], top["reason"]

    email_sent = False

    if conf >= threshold:
        task.assigned_to = emp
        task.status = "assigned"
        task.confidence_score = conf
        task.save()

        AssignmentLog.objects.create(
            task=task,
            reasoning_text=reason,
            confidence=conf,
            decision_status="auto_assigned"
        )
        logger.info(f"[Decision] Auto-assigned to {emp.name} (confidence {conf:.2f})")

        # Import inside function to avoid circular import issues
        from .notifications import send_assignment_email

        # Prepare email context for template rendering
        context = {
            "assignee_name": emp.name,
            "task_title": task.title,
            "task_description": task.description,
            "confidence_score": conf,
            "assigned_by": "AI Task Engine",
            "assigned_at": task.created_at.strftime("%Y-%m-%d %H:%M"),
            "task_url": f"{getattr(settings, 'FRONTEND_URL', '#')}/tasks/{task.id}",
            "summary_lines": [
                f"Confidence Score: {conf:.2f}",
                f"Reason: {reason}"
            ],
        }

        # Send the actual email
        try:
            send_assignment_email(emp.email, context)
            email_sent = True  # Mark as sent if successful
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            email_sent = False

    return {
        "decision": "auto_assign",
        "assignee": emp.name,
        "confidence": conf,
        "reason": reason,
        "email_sent": email_sent  # Add this to return value
    }

@shared_task
def run_assignment_pipeline(task_id: int, threshold: float = 0.75) -> dict:
    """
    End-to-end reasoning pipeline that mimics LangGraph execution flow,
    with confidence breakdown for frontend display.
    """
    task = Task.objects.get(pk=task_id)
    logger.info(f"🔹 Running AI assignment pipeline for Task ID={task.id}")

    # Step 1: Parse the task
    parsed = task_parser_node(task)

    # Step 2: Find matching candidates
    candidates = role_matching_node(parsed)
    if not candidates:
        return {
            "task": task.title,
            "recommended_assignee": None,
            "confidence_score": 0.0,
            "reasoning": "No candidates matched.",
            "confidence_breakdown": [],
            "email_sent": False  # Add this
        }

    # Step 3: Analyze workload
    candidate_info = workload_analyzer_node(candidates)

    # Step 4: Score confidence for each candidate
    scored = confidence_scorer_node(task, candidate_info)

    # Step 5: Make decision
    decision = decision_node(task, scored, threshold)

    # Build breakdown for chatbot UI
    breakdown = [
        {
            "name": s["employee"].name,
            "confidence": s["confidence"],
            "reason": s["reason"]
        }
        for s in scored
    ]

    # Build the final result payload
    result = {
        "task": task.title,
        "recommended_assignee": decision.get("assignee") or None,
        "confidence_score": float(task.confidence_score or 0.0),
        "reasoning": decision.get("reason", "See AssignmentLog."),
        "confidence_breakdown": breakdown,
        "email_sent": decision.get("email_sent", False)  # Add this
    }

    # Log the confidence breakdown in terminal (for better debugging)
    logger.info("🧠 Confidence Breakdown:")
    for b in breakdown:
        logger.info(f"• {b['name']}: {b['confidence']*100:.1f}% — {b['reason']}")

    logger.info(f"Final Assignment result: {result}")
    return result





def handle_chat_message(message: str) -> dict:
    """
    Handle conversational messages including greetings, questions, and task requests.
    Returns appropriate response based on message type.
    """
    if not message or not message.strip():
        return {
            "type": "error",
            "response": "I didn't receive any message. How can I help you?"
        }
   
    msg_lower = message.lower().strip()
   
    # --- Handle Greetings ---
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "howdy"]
    if any(msg_lower.startswith(greeting) or msg_lower == greeting for greeting in greetings):
        return {
            "type": "greeting",
            "response": "👋 Hello! I'm your AI Task Assignment Assistant. I can help you with:\n\n"
                       "• Creating and assigning tasks to team members\n"
                       "• Analyzing team workload and availability\n"
                       "• Providing assignment recommendations\n"
                       "• Checking task status and history\n\n"
                       "What would you like to do today?"
        }
   
    # --- Handle Help Requests ---
    help_keywords = ["help", "what can you do", "capabilities", "commands", "how to", "guide"]
    if any(keyword in msg_lower for keyword in help_keywords):
        return {
            "type": "help",
            "response": "🤖 **Here's what I can do:**\n\n"
                       "**Task Management:**\n"
                       "• Create tasks - I'll automatically analyze and assign them\n"
                       "• Review assignment confidence scores\n"
                       "• Check task status and history\n\n"
                       "**Team Intelligence:**\n"
                       "• Analyze employee skills and workload\n"
                       "• Recommend best assignees for tasks\n"
                       "• Balance team workload\n\n"
                       "**My AI Pipeline:**\n"
                       "1. Parse task requirements\n"
                       "2. Match with employee skills\n"
                       "3. Analyze workload\n"
                       "4. Calculate confidence scores\n"
                       "5. Auto-assign or recommend\n\n"
                       "Just create a task or ask me anything!"
        }
   
    # --- Handle Task/Assignment Status Queries ---
    status_keywords = ["show task", "list task", "task status", "assignments", "what tasks", "recent task"]
    if any(keyword in msg_lower for keyword in status_keywords):
        try:
            tasks = Task.objects.all().order_by("-created_at")[:5]
            if not tasks:
                return {
                    "type": "info",
                    "response": "📋 There are currently no tasks in the system. Would you like to create one?"
                }
           
            task_list = []
            for t in tasks:
                assignee = t.assigned_to.name if t.assigned_to else "Unassigned"
                confidence = f" (Confidence: {t.confidence_score:.0%})" if t.confidence_score else ""
                task_list.append(f"• **{t.title}** - {t.status.capitalize()}, {assignee}{confidence}")
           
            return {
                "type": "task_list",
                "response": f"📋 **Recent Tasks:**\n\n" + "\n".join(task_list) + f"\n\nTotal tasks: {Task.objects.count()}"
            }
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return {
                "type": "error",
                "response": "I encountered an error while fetching tasks. Please try again."
            }
   
    # --- Handle Employee/Team Queries ---
    team_keywords = ["employee", "team", "staff", "who is", "team member", "workers"]
    if any(keyword in msg_lower for keyword in team_keywords):
        try:
            employees = Employee.objects.all()[:10]
            if not employees:
                return {
                    "type": "info",
                    "response": "👥 There are no employees in the system yet."
                }
           
            emp_list = []
            for e in employees:
                workload_emoji = "🟢" if e.workload_score < 0.5 else "🟡" if e.workload_score < 0.8 else "🔴"
                emp_list.append(f"{workload_emoji} **{e.name}** ({e.role}) - Workload: {e.workload_score:.0%}")
           
            return {
                "type": "employee_list",
                "response": f"👥 **Team Members:**\n\n" + "\n".join(emp_list) + f"\n\nTotal employees: {Employee.objects.count()}"
            }
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return {
                "type": "error",
                "response": "I encountered an error while fetching employee information."
            }
   
    # --- Handle System/How It Works Queries ---
    if "how does" in msg_lower or "how do" in msg_lower or "explain" in msg_lower:
        return {
            "type": "explanation",
            "response": "🧠 **How the AI Assignment System Works:**\n\n"
                       "**Step 1: Task Parsing** 📝\n"
                       "I analyze your task title and description to extract keywords, required skills, and technical tags.\n\n"
                       "**Step 2: Role Matching** 🎯\n"
                       "I find employees whose skills and responsibilities match the task requirements.\n\n"
                       "**Step 3: Workload Analysis** ⚖️\n"
                       "I check each candidate's current workload to ensure balanced distribution.\n\n"
                       "**Step 4: Confidence Scoring** 💯\n"
                       "Using AI, I calculate how confident I am that each person is the right fit.\n\n"
                       "**Step 5: Decision** ✅\n"
                       "If confidence is high (≥75%), I auto-assign. Otherwise, I recommend for your review.\n\n"
                       "Plus, I send email notifications to assignees automatically!"
        }
   
    # --- Use LLM for General Conversational Queries ---
    llm = get_llm()
    if llm:
        try:
            # Get context about system
            task_count = Task.objects.count()
            employee_count = Employee.objects.count()
           
            context = f"""You are an AI assistant for an intelligent task assignment system.

System Overview:
- Total Tasks: {task_count}
- Total Employees: {employee_count}
- Your role: Help users understand the system, answer questions, and guide them

User Message: {message}

Instructions:
- Be helpful, friendly, and concise
- If asked about the system, explain its AI-powered task assignment capabilities
- If asked about specific tasks or employees, suggest they use specific queries
- Keep responses under 150 words

Respond naturally and helpfully."""
           
            result = llm.invoke(context)
            return {
                "type": "llm_response",
                "response": result.content
            }
        except Exception as e:
            logger.error(f"LLM failed for chat: {e}")
            # Fall through to default
   
    # --- Default Fallback ---
    return {
        "type": "default",
        "response": "I'm here to help with task assignments! 🤖\n\n"
                   "You can:\n"
                   "• Ask me 'help' to see what I can do\n"
                   "• Ask about 'tasks' or 'employees'\n"
                   "• Create a new task and I'll assign it intelligently\n\n"
                   "What would you like to do?"
    }