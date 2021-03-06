import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Tasks

# pewee -> jinja2 -> (pdfkit, wkhtmltopdf)

dir_path = os.path.dirname(os.path.realpath(__file__))

env = Environment(
    loader=FileSystemLoader(f"{dir_path}/templates"),
    autoescape=select_autoescape(["html"]),
)


def render_tasks(tasks):
    return env.get_template("all.html").render(tasks=tasks, pwd=dir_path)


__all__ = ["dir_path", "env", "render_tasks"]
