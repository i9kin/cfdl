import json
import time

import requests
from selenium import webdriver

from models import Solutions, Tasks, Tutorials

task_models = [task for task in Tasks.select()]

driver = webdriver.Chrome("./chromedriver")
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
driver.execute_script(s)
time.sleep(10)
task_map = driver.execute_script("return task_html")

for task in task_models:
    task.tutorial = task_map[task.id]
    task.save()
