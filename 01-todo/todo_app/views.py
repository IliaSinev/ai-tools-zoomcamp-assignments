from django.shortcuts import render
from .models import Task


def index(request):
    tasks = Task.objects.all().order_by("-created_at")
    context = {
        "tasks": tasks,
    }
    return render(request, "home.html", context)