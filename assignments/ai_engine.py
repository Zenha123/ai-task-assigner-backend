

import os
import json
import logging
from typing import Dict, Any, List
from django.conf import settings
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

