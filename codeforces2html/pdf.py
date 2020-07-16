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


def html(
    contests, additional_tasks, divs, letter_range, has_tutorial, has_code
):
    all_tasks = additional_tasks.copy() + get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]

    solutions_array = SolutionsArray(Solutions.select().dicts())
    tasks = Tasks.select().where(Tasks.id << [task for task in all_tasks])
    tasks = [task for task in tasks]

    m = {
        "1": ["Div. 1", "Div.1", "Див. 1", "Див.1"],
        "2": ["Div. 2", "Div.2", "Див. 2", "Див.2"],
        "3": ["Div. 3", "Div.3", "Див. 3", "Див.3"],
    }

    new = []
    for task in tasks:
        find = False
        for div in divs:
            for string in m[div]:
                if string in task.contest_title:
                    find = True
        if find and (
            ((has_tutorial and len(task.tutorial) != 0) or not has_tutorial)
            and ((has_code and len(task.solution) != 0) or not has_code)
        ):
            new.append(task)

    html = render_tasks(new, solutions_array)
    open("out.html", "w").write(html)


__all__ = ["dir_path", "env", "pdf", "render_tasks"]
