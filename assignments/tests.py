from django.test import TestCase
from .models import Employee, Task
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

class AssignmentFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Employee.objects.create(name="Dhruv", email="dhruv@example.com", role="Backend Engineer", skills=["python","django","api"], workload_score=0.2)
        Employee.objects.create(name="Manaal", email="manaal@example.com", role="PM", skills=["planning"], workload_score=0.6)

    @patch("assignment.ai_engine.get_llm")
    def test_create_task_triggers_assignment(self, mock_llm):
        # Mock LLM behaviour to avoid network calls
        class DummyLLM:
            def generate(self, prompts):
                class G:
                    text = '{"keywords":["api","upload"], "skills":["python","django"], "technical_tags":["api"], "effort_level":"medium"}'
                return type("R",(object,),{"generations":[[G()]]})
        mock_llm.return_value = DummyLLM()
        res = self.client.post("/api/tasks/", {"title":"Create API for uploading invoice PDFs", "description":"Upload PDFs", "created_by_id": None}, format="json")
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("assignment_result", data)
