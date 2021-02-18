import os
from typing import List, Tuple, Union

from lxml.html import HtmlElement, fromstring
from peewee import (
    BooleanField,
    CharField,
    Model,
    SqliteDatabase,
    TextField,
    chunked,
)

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


def clean_database():
    db.drop_tables([Tasks])
    db.create_tables([Tasks])


def delete_tasks(tasks_id):
    Tasks.delete().where(Tasks.id << tasks_id).execute()


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

    def add_tutorial(self, problemcode, html):
        self.TASK_SOLUTION[problemcode] = html

    def get_xhr_data(self, problemcode):
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


if __name__ == "__main__":
    clean_database()


__all__ = [
    "Data",
    "Statistic",
    "Tasks",
    "clean_database",
    "db",
    "delete_tasks",
    "dir_path",
]
