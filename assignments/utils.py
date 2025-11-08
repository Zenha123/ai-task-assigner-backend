from openai import OpenAI
import logging
from rest_framework.response import Response
from decouple import config as env

from .models import Task, Employee

logger = logging.getLogger(__name__)

OPENAI_API_KEY = env("OPENAI_API_KEY")

from rest_framework.response import Response

def handle_chat_message(message: str) -> Response:
    """
    Handle conversational messages including greetings, questions, and task requests.
    Returns appropriate response based on message type.
    """
    if not message or not message.strip():
        return Response({
            "type": "error",
            "response": "I didn't receive any message. How can I help you?"
        })

    msg_lower = message.lower().strip()

    # --- Handle Greetings ---
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "howdy"]
    if any(msg_lower.startswith(greeting) or msg_lower == greeting for greeting in greetings):
        return Response({
            "type": "greeting",
            "response": "👋 Hello! I'm your AI Task Assignment Assistant. I can help you with:\n\n"
                        "• Creating and assigning tasks to team members\n"
                        "• Analyzing team workload and availability\n"
                        "• Providing assignment recommendations\n"
                        "• Checking task status and history\n\n"
                        "What would you like to do today?"
        })

    # --- Handle Help Requests ---
    help_keywords = ["help", "what can you do", "capabilities", "commands", "how to", "guide"]
    if any(keyword in msg_lower for keyword in help_keywords):
        return Response({
            "type": "help",
            "response": "🤖 Here's what I can do:\n\n"
                        "Task Management:\n"
                        "• Create tasks - I'll automatically analyze and assign them\n"
                        "• Review assignment confidence scores\n"
                        "• Check task status and history\n\n"
                        "Team Intelligence:\n"
                        "• Analyze employee skills and workload\n"
                        "• Recommend best assignees for tasks\n"
                        "• Balance team workload\n\n"
                        "My AI Pipeline:\n"
                        "1. Parse task requirements\n"
                        "2. Match with employee skills\n"
                        "3. Analyze workload\n"
                        "4. Calculate confidence scores\n"
                        "5. Auto-assign or recommend\n\n"
                        "Just create a task or ask me anything!"
        })

    # --- Handle Task/Assignment Status Queries ---
    status_keywords = ["show task", "list task", "task status", "assignments", "what tasks", "recent task"]
    if any(keyword in msg_lower for keyword in status_keywords):
        try:
            tasks = Task.objects.all().order_by("-created_at")[:5]
            if not tasks:
                return Response({
                    "type": "info",
                    "response": "📋 There are currently no tasks in the system. Would you like to create one?"
                })

            task_list = []
            for t in tasks:
                assignee = t.assigned_to.name if t.assigned_to else "Unassigned"
                confidence = f" (Confidence: {t.confidence_score:.0%})" if t.confidence_score else ""
                task_list.append(f"• {t.title} - {t.status.capitalize()}, {assignee}{confidence}")

            return Response({
                "type": "task_list",
                "response": f"📋 Recent Tasks:\n\n" + "\n".join(task_list) + f"\n\nTotal tasks: {Task.objects.count()}"
            })
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return Response({
                "type": "error",
                "response": "I encountered an error while fetching tasks. Please try again."
            })

    # --- Handle Employee/Team Queries ---
    team_keywords = ["employee", "team", "staff", "who is", "team member", "workers"]
    if any(keyword in msg_lower for keyword in team_keywords):
        try:
            employees = Employee.objects.all()[:10]
            if not employees:
                return Response({
                    "type": "info",
                    "response": "👥 There are no employees in the system yet."
                })

            emp_list = []
            for e in employees:
                workload_emoji = "🟢" if e.workload_score < 0.5 else "🟡" if e.workload_score < 0.8 else "🔴"
                emp_list.append(f"{workload_emoji} {e.name} ({e.role}) - Workload: {e.workload_score:.0%}")

            return Response({
                "type": "employee_list",
                "response": f"👥 Team Members:\n\n" + "\n".join(emp_list) + f"\n\nTotal employees: {Employee.objects.count()}"
            })
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return Response({
                "type": "error",
                "response": "I encountered an error while fetching employee information."
            })

    # --- Handle System/How It Works Queries ---
    if "how does" in msg_lower or "how do" in msg_lower or "explain" in msg_lower:
        return Response({
            "type": "explanation",
            "response": "🧠 How the AI Assignment System Works:\n\n"
                        "Step 1: Task Parsing 📝\n"
                        "I analyze your task title and description to extract keywords, required skills, and technical tags.\n\n"
                        "Step 2: Role Matching 🎯\n"
                        "I find employees whose skills and responsibilities match the task requirements.\n\n"
                        "Step 3: Workload Analysis ⚖️\n"
                        "I check each candidate's current workload to ensure balanced distribution.\n\n"
                        "Step 4: Confidence Scoring 💯\n"
                        "Using AI, I calculate how confident I am that each person is the right fit.\n\n"
                        "Step 5: Decision ✅\n"
                        "If confidence is high (≥75%), I auto-assign. Otherwise, I recommend for your review.\n\n"
                        "Plus, I send email notifications to assignees automatically!"
        })

    # --- Default Fallback ---
    return Response({
        "type": "default",
        "response": "I'm here to help with task assignments! 🤖\n\n"
                    "You can:\n"
                    "• Ask me 'help' to see what I can do\n"
                    "• Ask about 'tasks' or 'employees'\n"
                    "• Create a new task and I'll assign it intelligently\n\n"
                    "What would you like to do?"
    })


client = OpenAI(api_key=OPENAI_API_KEY)

def classify_message_openai(message: str) -> dict:
    """
    Uses OpenAI to classify the message type: 'greeting', 'help', 'task', 'unknown'.
    Returns a dict with 'type' and 'response' (optional for non-task messages).
    """
    try:
        prompt = f"""
            Classify the following message into one of these categories: 
            'greeting', 'help', 'task', 'unknown'.
            Return only the category name. Message: "{message}"
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that classifies messages into types."},
                {"role": "user", "content": prompt},
            ],
            temperature=0
        )

        category = response.choices[0].message.content.strip().lower()

        # Safety fallback
        if category not in ["greeting", "help", "task", "unknown"]:
            category = "unknown"

        logger.info(f"🔹 OpenAI classified message as: {category}")
        return handle_chat_message(message) if category != "task" else {"type": "task"}
    except Exception as e:
        logger.error(f"Error classifying message via OpenAI: {e}")
        return {"type": "unknown"}