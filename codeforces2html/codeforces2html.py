from .aio import parse
from .bar_utils import Bar
from .models import SolutionsArray, refresh
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

    return task_array, solutions.get_array()


def main(contests, tasks, debug=True):
    global REQUESTS
    TASKS, last_contest = problemset()
    REQUESTS = parse(contests, tasks, debug)
    ALL_TASKS = []
    ALL_SOLUTIONS = []

    if len(contests) != 0:
        PROGRESS_BAR = Bar(contests, debug=debug)
        for contest in PROGRESS_BAR:
            PROGRESS_BAR.set_description("download contest %s" % contest)
            task_array, solution_array = parse_contest(contest, TASKS[contest])
            for task in task_array:
                ALL_TASKS.append(task)
            for solution in solution_array:
                ALL_SOLUTIONS.append(solution)
    if len(tasks) != 0:
        PROGRESS_BAR = Bar(tasks, debug=debug)
        for contest_id, task_leter in PROGRESS_BAR:
            PROGRESS_BAR.set_description(
                f"download task {contest_id}{task_leter}"
            )

            problem, name, tags = None, None, None
            for t in TASKS[contest_id]:
                if t[0] == task_leter:
                    problem, name, tags = t
                    break
            task = parse_task(contest_id, problem, name, tags, None)

            solutions = REQUESTS.get_blog(contest_id)

            if solutions == []:
                solutions = SolutionsArray([])
            solution_array = solutions[f"{contest_id}{task_leter}"]

            task["solution"] = ",".join(
                [solution["solution_id"] for solution in solution_array]
            )
            ALL_TASKS.append(task)

            for solution in solution_array:
                ALL_SOLUTIONS.append(solution)

    refresh(ALL_TASKS, ALL_SOLUTIONS)


__all__ = ["REQUESTS", "main", "parse_contest", "parse_task"]
