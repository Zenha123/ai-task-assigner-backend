from django.core.management.base import BaseCommand
from assignments.models import Employee
import json

class Command(BaseCommand):
    help = "Import roles & responsibilities JSON into Employee model"

    def add_arguments(self, parser):
        parser.add_argument('jsonfile', type=str)

    def handle(self, *args, **options):
        path = options['jsonfile']
        with open(path, 'r') as f:
            data = json.load(f)
        for item in data:
            Employee.objects.update_or_create(email=item['email'], defaults={
                'name': item.get('name'),
                'role': item.get('role'),
                'skills': item.get('skills', []),
                'responsibilities': item.get('responsibilities', ''),
                'workload_score': item.get('workload_score', 0.0)
            })
        self.stdout.write(self.style.SUCCESS("Imported roles successfully."))
