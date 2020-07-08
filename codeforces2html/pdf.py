import os
import webbrowser

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


solutions_array = SolutionsArray(Solutions.select().dicts())
tasks = Tasks.select()


def render_task(task):
    return env.get_template("one.html").render(
        task=task, solutions=solutions_array[task.id], pwd=dir_path
    )


def render_tasks(tasks):
    return env.get_template("all.html").render(
        tasks=tasks, solutions_array=solutions_array, pwd=dir_path
    )


def pdf(contests, additional_tasks):
    print(contests, additional_tasks)
    all_tasks = additional_tasks.copy() + get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]
    tasks = Tasks.select().where(Tasks.id << [task for task in all_tasks])
    tasks = [task for task in tasks]
    options = {
        "page-size": "Letter",
        "no-outline": None,
        "javascript-delay": 2 * len(tasks) * 1000,
    }
    html = render_tasks(tasks)
    pdfkit.from_string(html, "out.pdf", options=options)
