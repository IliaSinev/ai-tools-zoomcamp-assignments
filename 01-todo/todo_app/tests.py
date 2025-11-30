from django.test import TestCase
from django.urls import reverse
from .models import Task


class TaskModelTests(TestCase):
    def test_task_creation(self):
        task = Task.objects.create(title="Test task")
        self.assertEqual(task.title, "Test task")
        self.assertFalse(task.is_done)
        self.assertIsNotNone(task.created_at)

    def test_string_representation(self):
        task = Task.objects.create(title="My task")
        self.assertEqual(str(task), "My task")


class HomeViewTests(TestCase):
    def test_home_page_status_code(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")

    def test_home_page_shows_no_tasks_message(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "No tasks yet.")

    def test_home_page_lists_existing_tasks(self):
        Task.objects.create(title="Task 1")
        Task.objects.create(title="Task 2")

        response = self.client.get(reverse("home"))
        self.assertContains(response, "Task 1")
        self.assertContains(response, "Task 2")