import os
import webbrowser

from jinja2 import Environment, FileSystemLoader, select_autoescape

import pdfkit
from models import Solutions, SolutionsArray, Tasks

# pewee -> jinja2 -> (pdfkit, wkhtmltopdf)
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

pwd = os.getcwd()

solutions_array = SolutionsArray(Solutions.select().dicts())
tasks = Tasks.select()


def render_task(task):
    return env.get_template("one.html").render(
        task=task, solutions=solutions_array[task.id], pwd=pwd
    )


def render_tasks(tasks):
    return env.get_template("all.html").render(
        tasks=tasks, solutions_array=solutions_array, pwd=pwd
    )


tasks = [task for task in Tasks.select()]


options = {
    "page-size": "Letter",
    "no-outline": None,
    "javascript-delay": 2 * len(tasks) * 1000,
}
# html = render_tasks(tasks[:100])
# pdfkit.from_string(html, 'out.pdf',  options=options)


html_ = []
c = []
i = 0
for task in tasks:
    i += 1
    html = render_task(task)
    open(f"tmp/{i}.html", "w").write(html)
    c.append(f"tmp/{i}.html")

pdfkit.from_file(c, "out.pdf", options=options)
