import asyncio
import time

from peewee import chunked
from tqdm import tqdm

from .aio import AIO, parse
from .models import Solutions, SolutionsArray, Tasks, clean, db, refresh
from .utils import get_condition, get_contest_title, problemset

REQUESTS = None


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


def parse_contest(contest, contest_array):
    task_array = []
    solutions = REQUESTS.get_blog(contest)
    if solutions == []:
        solutions = SolutionsArray([])
    contest_title = None
    for i, (problem, name, tags) in enumerate(contest_array):
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


def main(contests, tasks, tqdm_debug=True):
    global REQUESTS
    tasks = list(tasks)

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

    TASKS, last_contest = problemset()

    clean_contests = []
    for contest in contests:
        if contest in TASKS and contest not in ISSUES:
            clean_contests.append(contest)
    clean_tasks = []

    for task in tasks:
        for i, char in enumerate(task):
            if not char.isdigit() and int(task[:i]) not in ISSUES:
                clean_tasks.append([int(task[:i]), task[i:]])
                break

    REQUESTS = parse(clean_contests, clean_tasks, tqdm_debug)
    if tqdm_debug:
        PROGRESS_BAR = tqdm(
            clean_contests,
            ascii=" ━",
            bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
        )
    else:
        PROGRESS_BAR = clean_contests

    ALL_TASKS = []
    ALL_SOLUTIONS = []

    for contest in PROGRESS_BAR:
        if tqdm_debug:
            PROGRESS_BAR.set_description("download contest %s" % contest)
        task_array, solution_array = parse_contest(contest, TASKS[contest])
        for task in task_array:
            ALL_TASKS.append(task)
        for solution in solution_array:
            ALL_SOLUTIONS.append(solution)
    if tqdm_debug:
        PROGRESS_BAR = tqdm(
            clean_tasks,
            ascii=" ━",
            bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
        )
    else:
        PROGRESS_BAR = clean_tasks

    for task in PROGRESS_BAR:
        if tqdm_debug:
            PROGRESS_BAR.set_description(f"download task {task[0]}{task[1]}")
        contest, task_leter = task

        problem, name, tags = None, None, None
        for t in TASKS[contest]:
            if t[0] == task_leter:
                problem, name, tags = t
                break
        ALL_TASKS.append(parse_task(contest, problem, name, tags, None))

    refresh(ALL_TASKS, ALL_SOLUTIONS)


if __name__ == "__main__":
    main()
