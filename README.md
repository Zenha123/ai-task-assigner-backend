# 🤖 AI Task Assignment System

**Automated Employee Task Assignment & Intelligence Pipeline**  
A Django–React-LangGraph–Celery–Docker-based system for intelligent task distribution using AI-driven matching and confidence scoring.

---

## 🚀 Project Overview

The **AI Task Assignment System** automates project task analysis and assignment to employees based on skills, workload, and past performance.  
It integrates **LangGraph, OpenAI, and Celery** to build an intelligent, asynchronous task assignment engine that mimics real-world reasoning.

**Key Features:**

- 🧠 AI-driven task parsing and employee matching  
- 📊 Confidence-based assignment scoring  
- 📧 Automatic assignment email notifications  
- 🔄 Real-time task updates via REST API  
- 🧩 Built with Django, React, LangGraph, Celery, and PostgreSQL  
- 🐳 Full Docker support for backend, frontend, Redis, and worker  
- 🌐 Hosted Backend on Azure & Frontend on Vercel


## 🛠️ Tech Stack

| Layer                  | Technology                                    |
|------------------------|-----------------------------------------------|
| Backend                | Django, Django REST Framework                 |
| Frontend               | React + TailwindCSS                           |
| Database               | PostgreSQL                                    |
| Task Queue             | Celery + Redis                                |
| AI Reasoning Engine    | LangGraph + OpenAI API                        |
| Containerization       | Docker + Docker Compose                        |
| Email Notification     | SMTP (localhost)                              |

---
## 🐰 Development Setup (Manual Run)

# Backend (Django):
```
git clone https://github.com/Zenha123/ai-task-assignment-system.git
cd ai-task-assignment-system
python -m venv env
env\Scripts\activate       # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

# Frontend (React):
```
git clone [https://github.com/Zenha123/ai-task-assignment-system.git](https://github.com/Zenha123/ai-task-assigner-frontend.git)
cd ai-task-assigner-frontend
npm install
npm run dev
```

## Access After Build:
 ## 🌐 Local
-Frontend: http://localhost:5173

-Backend API: http://localhost:8000/api

-Admin Panel: http://localhost:8000/admin


## ⚛️ Frontend UI Overview

💬 AI Chat Interface – Describe tasks in plain English

🧑‍💻 Dashboard – Displays tasks, assigned employee, confidence, and status

📧 Assignment Notifications – Sent automatically via SMTP


## 🌐 Hosting

Backend (Azure): https://ai-task-assigner-cfc8ewape0dmdmd2.westus-01.azurewebsites.net/api/schema/swagger-ui/

Frontend (Vercel): https://ai-task-assigner-frontend.vercel.app/

## ⚙️ Core Modules Overview

### Employee

| Field          | Type       | Description                       |
|----------------|-----------|-----------------------------------|
| name           | CharField | Employee name                     |
| role           | CharField | Role or designation               |
| email          | EmailField| Used for task notifications       |
| skills         | JSON      | List of skills                    |
| workload_score | Float     | Current workload indicator        |

### Task

| Field        | Type          | Description                                  |
|--------------|---------------|----------------------------------------------|
| title        | CharField     | Task title                                   |
| description  | TextField     | Task details                                 |
| priority     | ChoiceField   | Low / Medium / High                          |
| status       | ChoiceField   | Open / Assigned / In Progress / Done        |
| assigned_to  | ForeignKey    | Linked Employee                              |
| confidence_score | Float     | Assignment confidence                        |
| created_by   | ForeignKey    | Task creator                                 |
| created_at   | DateTime      | Created timestamp                            |

### AssignmentLog

| Field           | Type       | Description                     |
|-----------------|-----------|---------------------------------|
| task            | ForeignKey| Linked task                     |
| confidence      | Float     | Confidence score                |
| reasoning_text  | Text      | Reason for decision             |
| decision_status | CharField | auto_assigned / review / no_candidates |

---

## 🔗 API Endpoints

| Endpoint           | Method | Description                       |
|-------------------|--------|-----------------------------------|
| /api/employees/   | GET    | List all employees                |
| /api/tasks/       | GET    | List all tasks                    |
| /api/tasks/       | POST   | Create and auto-assign a new task|
| /api/logs/        | GET    | Retrieve assignment logs          |

---

## 🧩 AI Assignment Workflow

1. **Task Parsing** – Uses LangGraph + OpenAI to extract key skills and keywords from task title and description.  
2. **Candidate Matching** – Compares parsed skills with employee data to find best matches.  
3. **Workload Analysis** – Adjusts matching score based on employee workload.  
4. **Confidence Scoring** – Generates AI-based confidence and reasoning for each candidate.  
5. **Decision & Assignment** – Assigns task automatically if confidence ≥ threshold; otherwise flags for review.  
6. **Notification** – Sends assignment email with details (works on localhost via SMTP).  

**Example AI Output:**
```
Task: Build a REST API in Django to manage project reports and store them in PostgreSQL
AI Response:

✅ Task assigned to Dhruv Sharma with confidence 85.0%.

Reason: Dhruv has relevant skills in Python, Django, and PostgreSQL.

🧠 Confidence Breakdown:
• Dhruv Sharma: 85.0% — Strong Django & PostgreSQL background
• Simran Kaur: 30.0% — Focused on DevOps, limited Django experience
• Arjun Mehta: 10.0% — Management-focused, lacks backend development experience

📧 Assignment email sent to dhruv.sharma@example.com

```

🐳 Docker Setup
```bash
docker-compose up --build
docker run
docker start
```
