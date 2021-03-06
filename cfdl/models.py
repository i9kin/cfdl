import os
from typing import List, Tuple, Union

from lxml.html import HtmlElement, fromstring
from peewee import (BooleanField, CharField, IntegerField, Model,
                    SqliteDatabase, TextField, chunked)

from .utils import get_type

dir_path = os.path.dirname(os.path.realpath(__file__))

db = SqliteDatabase(f"{dir_path}/cf.sqlite")


class Tasks(Model):

    id = CharField(max_length=15)
    name = CharField(max_length=100)  # название
    contest_title = CharField(max_length=100)

    condition = TextField()  # условие
    tutorial = TextField()  # разбор
    tags = TextField()  # теги задачи

    materials = None

    class Meta:

        database = db
        db_table = "tasks"


class Statistic(Model):

    id = CharField(max_length=15)
    is_solved = BooleanField(default=False)

    class Meta:

        database = db
        db_table = "statistic"


class Contests(Model):

    name = CharField(max_length=100)
    contest_id = IntegerField()
    type = CharField(max_length=100)

    class Meta:
        database = db
        db_table = "contests"


def clean_database():
    db.drop_tables([Tasks, Contests])
    db.create_tables([Tasks, Contests])


def delete_tasks(tasks_id):
    Tasks.delete().where(Tasks.id << tasks_id).execute()


def clean_contests():
    db.drop_tables([Contests])
    db.create_tables([Contests])


class Data:
    """class for saving data."""

    def __init__(self):
        self.TASKS = []
        self.XHR_DATA = {}
        self.TASK_SOLUTION = {}
        self.TASK_TREE = {}

    def add_task_tree(
        self, contest_id: int, letter: str, tree: HtmlElement
    ) -> None:
        if contest_id not in self.TASK_TREE:
            self.TASK_TREE[contest_id] = {}
        self.TASK_TREE[contest_id][letter] = tree

    def get_task_tree(self, contest_id: int, task_letter: str) -> HtmlElement:
        return self.TASK_TREE[contest_id][task_letter]

    def add_json_task(self, task):
        self.TASKS.append(task)

    def add_blog_tree(self):
        pass

    def add_xhr_data(self, data):
        self.XHR_DATA[data[0]] = data[1]

    def add_tutorial(self, problemcode, html, blog_url):
        html = f'<div class="spoiler"><b class="spoiler-title">{blog_url}</b><div class="spoiler-content" style="display: none;">{html}</div></div>'
        if problemcode not in self.TASK_SOLUTION:
            self.TASK_SOLUTION[problemcode] = html
        else:
            self.TASK_SOLUTION[problemcode] += html

    def get_xhr_data(self, problemcode):
        if problemcode not in self.XHR_DATA:
            return None
        else:
            return self.XHR_DATA[problemcode]

    def set_tutorials(self):
        for task in self.TASKS:
            if task["id"] in self.TASK_SOLUTION:
                task["tutorial"] = self.TASK_SOLUTION[task["id"]]

    def save(self):
        self.set_tutorials()
        delete_tasks([task["id"] for task in self.TASKS])
        with db.atomic():
            for batch in chunked(self.TASKS, 1000):
                Tasks.insert_many(batch).execute()


from json import dumps


def save_contests(contests):
    data = []

    for contest_name, contest_id in contests:
        data.append(
            {
                "contest_id": str(contest_id),
                "name": contest_name,
                "type": dumps(get_type(contest_id, contest_name)),
            }
        )

    with db.atomic():
        for batch in chunked(data, 1000):
            Contests.insert_many(batch).execute()


if __name__ == "__main__":
    clean_database()


__all__ = [
    "Contests",
    "Data",
    "Statistic",
    "Tasks",
    "clean_database",
    "db",
    "delete_tasks",
    "dir_path",
    "save_contests",
]
