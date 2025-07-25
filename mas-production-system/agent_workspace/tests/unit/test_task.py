from django.test import TestCase
from ..models.task import Task

class TaskModelTest(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title='Test Task', description='A task for testing.')

    def test_task_creation(self):
        self.assertEqual(str(self.task), 'Test Task')