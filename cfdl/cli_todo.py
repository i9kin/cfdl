from __future__ import print_function, unicode_literals

from prompt_toolkit.validation import ValidationError, Validator
from PyInquirer import Separator, print_json, prompt
from rich import print as rprint
from rich.columns import Columns
from rich.panel import Panel

from .models import Statistic, Tasks
from .utils import get_contest, get_letter


class NumberValidator(Validator):
    def validate(self, document):
        exp = ValidationError(
            message="Please enter a number", cursor_position=len(document.text)
        )
        if document.text.isdecimal():
            contest_id = int(document.text)
            tasks = [task for task in Tasks.select()]
            ids = set()
            for task in tasks:
                ids.add(int(get_contest(task.id)))
            if contest_id not in ids:
                raise exp
        else:
            raise exp


def get_choices(contest_id):
    tasks = [task for task in Statistic.select()]
    contest_task = []
    for task in tasks:
        id_ = int(get_contest(task.id))
        if id_ == contest_id:
            contest_task.append(task)
    contest_task.sort(key=lambda x: x.id)
    return contest_task


def create_tasks():
    statistic_id = set([item.id for item in Statistic.select()])
    task_id = set([task.id for task in Tasks().select()])
    for item in task_id - statistic_id:
        Statistic.create(id=item)


def cli_task(contest_id):
    contest_task = get_choices(contest_id)

    yes = []
    no = []

    choices = []
    for task in contest_task:
        if task.is_solved:
            yes.append(task)
        else:
            no.append(task)
        choices.append({"checked": task.is_solved, "name": task.id})

    q = prompt(
        [
            {
                "type": "checkbox",
                "qmark": "😃",
                "message": "Select task",
                "name": "items",
                "choices": choices,
            }
        ]
    )
    if q == {}:
        exit(0)
    checked_items = q["items"]

    for item in yes:
        if item.id not in checked_items:
            item.is_solved = False
            item.save()

    for item in no:
        if item.id in checked_items:
            item.is_solved = True
            item.save()


def cli_contest():
    q = prompt(
        [
            {
                "type": "input",
                "name": "n",
                "message": "Input number of contest",
                "validate": NumberValidator,
                "filter": lambda val: int(val),
            },
        ]
    )
    if q == {}:
        exit(0)
    return q["n"]


def get_content(tasks):
    s = f"[bold]{get_contest(tasks[0].id)}[/]"
    for task in tasks:
        s += f"[{'green' if task.is_solved else 'red'} bold]{get_letter(task.id)}[/]"
    return s


def main():
    create_tasks()
    q = prompt(
        [
            {
                "type": "list",
                "name": "command",
                "message": "What do you want to do?",
                "choices": ["Mark tasks", "View cards",],
            }
        ]
    )
    if q == {}:
        exit(0)
    command = q["command"]
    if command == "Mark tasks":
        contest_id = cli_contest()
        cli_task(contest_id)
    else:
        contest = {}
        for task in Statistic.select():
            id = get_contest(task.id)
            if id not in contest:
                contest[id] = []
            contest[id].append(task)

        for id in contest:
            contest[id].sort(key=lambda x: x.id)

        keys = sorted(list(contest.keys()), reverse=True)

        user_renderables = [
            Panel(get_content(contest[tasks]), expand=True) for tasks in keys
        ]
        rprint(Columns(user_renderables))


__all__ = [
    "NumberValidator",
    "cli_contest",
    "cli_task",
    "create_tasks",
    "get_choices",
    "get_content",
    "main",
]
