import os
from typing import List, Tuple, Union

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
    solution = TextField()  # решение
    tags = TextField()  # теги задачи

    materials = None

    class Meta:

        database = db
        db_table = "codeforces"


class Solutions(Model):
    solution_id = CharField(max_length=100)  # 1358F[1/2/3]
    solution = TextField()  # решение

    class Meta:

        database = db
        db_table = "solutions"


class Tutorials(Model):
    tutorial_id = CharField(max_length=100)  # 1358F[1/2/3]
    tutorial = TextField()  # идяе решения

    class Meta:

        database = db
        db_table = "tutorial"


class Statistic(Model):

    id = CharField(max_length=15)
    is_solved = BooleanField(default=False)

    class Meta:

        database = db
        db_table = "statistic"


class SolutionsArray:
    # parse_blog return string for sql (for fast query)
    # Solutions.select().where(Solutions.solution_id.startswith('1361A'))
    # key : string '1361A' val: '1361A[0],...'

    def __init__(self, array, urls=None):

        if urls is None:
            urls = {}

        self.m = {}
        self.urls = urls
        for model in array:
            s = model["solution_id"][: model["solution_id"].find("[")]
            if s not in self.m:
                self.m[s] = [model]
            else:
                self.m[s].append(model)

    def __getitem__(self, key):
        if key in self.m:
            return self.m[key]
        else:
            return []

    def __str__(self):
        return str(len(self.m))

    def update(self, problemcode, submition):
        if problemcode not in self.m:
            self.m[problemcode] = [
                {"solution_id": problemcode + "[0]", "solution": submition}
            ]
        else:
            self.m[problemcode].append(
                {
                    "solution_id": f"{problemcode}[{len(self.m[problemcode])}]",
                    "solution": submition,
                }
            )

    def get_array(self):
        array = []
        for problemcode in self.m:
            for model in self.m[problemcode]:
                array.append(model)
        return array


def clean_database():
    db.drop_tables([Tasks, Solutions])
    db.create_tables([Tasks, Solutions])


def delete_tasks(tasks_id):
    Tasks.delete().where(Tasks.id << tasks_id).execute()


def delete_solutions(solutions_id):
    Solutions.delete().where(Solutions.solution_id << solutions_id).execute()


ALL_TASKS, ALL_SOLUTIONS = [], []


def update(tasks, solutions):
    global ALL_TASKS, ALL_SOLUTIONS
    ALL_TASKS, ALL_SOLUTIONS = tasks, solutions


def update_tutorials(tutorials: List[Tuple[str, str]]):
    global ALL_TASKS
    tutorials_map = {}
    for task_id, tutorial in tutorials:
        tutorials_map[task_id] = tutorial
    for task in ALL_TASKS:
        if task["id"] in tutorials_map:
            task["tutorial"] = tutorials_map[task["id"]]


def fast_insert():
    global ALL_TASKS, ALL_SOLUTIONS
    delete_tasks([task["id"] for task in ALL_TASKS])
    delete_solutions([solution["solution_id"] for solution in ALL_SOLUTIONS])

    with db.atomic():
        for batch in chunked(ALL_SOLUTIONS, 1000):
            Solutions.insert_many(batch).execute()

    with db.atomic():
        for batch in chunked(ALL_TASKS, 1000):
            Tasks.insert_many(batch).execute()


if __name__ == "__main__":
    clean_database()


__all__ = [
    "Solutions",
    "SolutionsArray",
    "Tasks",
    "Tutorials",
    "clean_database",
    "db",
    "dir_path",
    "refresh",
]
