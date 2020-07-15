import os

import pdfkit
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Solutions, SolutionsArray, Tasks
from .utils import get_tasks

# pewee -> jinja2 -> (pdfkit, wkhtmltopdf)

dir_path = os.path.dirname(os.path.realpath(__file__))

env = Environment(
    loader=FileSystemLoader(f"{dir_path}/templates"),
    autoescape=select_autoescape(["html"]),
)


def render_tasks(tasks, solutions_array):
    return env.get_template("all.html").render(
        tasks=tasks, solutions_array=solutions_array, pwd=dir_path
    )


def pdf(contests, additional_tasks):
    all_tasks = additional_tasks.copy() + get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]

    solutions_array = SolutionsArray(Solutions.select().dicts())
    tasks = Tasks.select().where(Tasks.id << [task for task in all_tasks])
    tasks = [task for task in tasks]
    options = {
        "page-size": "Letter",
        "no-outline": None,
        "javascript-delay": 2 * len(tasks) * 1000,
    }
    html = render_tasks(tasks, solutions_array)
    pdfkit.from_string(html, "out.pdf", options=options)

def html(contests, additional_tasks, tasks_range):
    all_tasks = additional_tasks.copy() + get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]

    solutions_array = SolutionsArray(Solutions.select().dicts())
    tasks = Tasks.select().where(Tasks.id << [task for task in all_tasks])
    tasks = [task for task in tasks]

    new = []
    for task in tasks:
        if 'Див. 2' in task.contest_title or 'Div. 2' in task.contest_title:
            if len(task.tutorial) != 0:
                for i, char in enumerate(task.id):
                    if not char.isdigit():
                        id = task.id[i:]
                        break

                if id in tasks_range:
                    new.append(task)

    options = {
        "page-size": "Letter",
        "no-outline": None,
        "javascript-delay": 2 * len(new) * 1000,
    }
    html = render_tasks(new, solutions_array)
    pdfkit.from_string(html, "out.pdf", options=options)

__all__ = ["dir_path", "env", "pdf", "render_tasks"]
