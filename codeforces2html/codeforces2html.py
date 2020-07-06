import asyncio
import time

from peewee import chunked
from tqdm import tqdm

from .aio import parse
from .models import Solutions, SolutionsArray, Tasks, clean, db
from .utils import get_condition, get_contest_title, problemset


def parse_task(contest, problem, name, tags, contest_title):
    tree = REQUESTS.get_task(contest, problem)
    obj = {
        "id": f"{contest}{problem}",
        "name": name,
        "contest_title": get_contest_title(tree)
        if contest_title is None
        else contest_title,
        "condition": get_condition(tree),
        "tutorial": "",
        "solution": "",
        "tags": ", ".join(tags),
    }
    return obj


def parse_contest(contest):
    task_array = []
    solutions = REQUESTS.get_blog(contest)
    if solutions == []:
        solutions = SolutionsArray([])
    contest_title = None
    for i, (problem, name, tags) in enumerate(TASKS[contest]):
        task = parse_task(contest, problem, name, tags, contest_title)
        if i == 0:
            contest_title = task["contest_title"]
        task["solution"] = ",".join(
            [
                solution["solution_id"]
                for solution in solutions[f"{contest}{problem}"]
            ]
        )
        task_array.append(task)
    return task_array, solutions.array


clean()
contests = {1363, 1367}
tasks = {"1367A"}


CONTEST_RANGE = 2
REQUESTS = parse(contests, 0)

TASKS, last_contest = problemset()

OLD_ISSUES = [
    1252,  # (решение pdf (ICPC))
    1218,  # Bubble Cup 12 (решение pdf)
    1219,  # Bubble Cup 12 (решение pdf)
]

ISSUES = [
    1267,  # (задачи + решение pdf (ICPC))
    1208,  # (problemTutorial не везде)
    1191,  # (problemTutorial нет)
    1190,  # (problemTutorial нет)
    1184,  # (решение pdf)
    1172,  # (problemTutorial нет)
    1173,  # (problemTutorial нет)
    1153,  # (problemTutorial нет)
    1129,
]

# div1 + div2 https://codeforces.com/blog/entry/78355?locale=ru

CONTESTS = []
for contest in contests:
    if contest in TASKS:
        CONTESTS.append(contest)

PROGRESS_BAR = tqdm(
    CONTESTS,
    ascii=" ━",
    bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
)

ALL_TASKS = []
ALL_SOLUTIONS = []

for contest in PROGRESS_BAR:
    PROGRESS_BAR.set_description("contest %s" % contest)
    if contest not in ISSUES:
        task_array, solution_array = parse_contest(contest)
        for task in task_array:
            ALL_TASKS.append(task)
        for solution in solution_array:
            ALL_SOLUTIONS.append(solution)
    time.sleep(0.1)

# delete old

Tasks.delete().where(Tasks.id << [task["id"] for task in ALL_TASKS]).execute()
Solutions.delete().where(
    Solutions.solution_id
    << [solution["solution_id"] for solution in ALL_SOLUTIONS]
).execute()


with db.atomic():
    for batch in chunked(ALL_SOLUTIONS, 100):
        Solutions.insert_many(batch).execute()


with db.atomic():
    for batch in chunked(ALL_TASKS, 100):
        Tasks.insert_many(batch).execute()
