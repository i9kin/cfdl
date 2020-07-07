import json
import time
import os
from selenium import webdriver

from .models import Solutions, Tasks, Tutorials
from .utils import TASKS


def main():

    contests, additional_tasks = [1365, 1366, 1367], [[1362, "A"]]

    all_tasks = []

    for task in additional_tasks:
        all_tasks.append(f"{task[0]}{task[1]}")

    for contest in contests:
        for task, _, _ in TASKS[contest]:
            all_tasks.append(f"{contest}{task}")

    task_models = Tasks.select().where(
        Tasks.id << [task for task in all_tasks]
    )

    dir_path = os.path.dirname(os.path.realpath(__file__))

    driver = webdriver.Chrome(f"{dir_path}/chromedriver")
    driver.get("https://codeforces.com/topic/73635/")

    javascript_function = """
    task_html = {}
    function load_task(problemCode) {
        return $.post('https://codeforces.com/data/problemTutorial', {
            problemCode: problemCode
        }, function(data) {
          task_html[problemCode] = data["html"];
        }, "json");
    }
    """

    javascript_exctract = """
    for (code in problem_codes) {
        load_task(problem_codes[code])
    }
    """
    s = f"""
    {javascript_function}
    problem_codes = {[task.id for task in task_models]}
    {javascript_exctract}
    """
    print(s, [task.id for task in task_models])
    driver.execute_script(s)
    time.sleep(10)
    task_map = driver.execute_script("return task_html")
    print([k for k in task_map])

    for task in task_models:
        task.tutorial = task_map[task.id]
        task.save()
