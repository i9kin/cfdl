import json
import os

from lxml import html
from lxml.etree import tostring

from .models import Solutions, SolutionsArray

dir_path = os.path.dirname(os.path.realpath(__file__))


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


def problemset():
    # 'https://codeforces.com/api/problemset.problems'
    data = json.load(open(f"{dir_path}/problemset.txt", "r"))["result"][
        "problems"
    ]

    last_contest = data[0]["contestId"]
    tasks = {}
    for task in data:
        id = task["contestId"]
        index = task["index"]
        tags = task["tags"]
        name = task["name"]
        if id not in tasks:
            tasks[id] = [[index, name, tags]]
        else:
            tasks[id].append([index, name, tags])
    return tasks, last_contest


def get_condition(tree):
    task_element = tree.xpath('//*[@id="pageContent"]/div[2]')[0]
    return tostring(task_element, encoding="utf-8").decode("utf-8")


def get_contest_title(tree):
    contest_xpath = '//*[@id="sidebar"]/div[1]/table/tbody/tr[1]/th/a'
    return tree.xpath(contest_xpath)[0].text_content()


def materials(tree):
    materials_xpath = '//*[@id="sidebar"]/div[4]/ul/li/span[1]/a'
    materials = tree.xpath(materials_xpath)
    if len(materials) == 0:
        materials_xpath = '//*[@id="sidebar"]/div[5]/ul/li/span[1]/a'
        materials = tree.xpath(materials_xpath)
    material_link = None
    for material in materials:
        if "Разбор задач" in material.text_content():
            material_link = material.get("href")
    if material_link is None:
        return None
    return material_link.split("/")[-1]


def parse_blog(tree):
    childrens = tree.xpath('//*[@id="pageContent"]/div/div/div/div[3]/div')[
        0
    ].getchildren()
    solutions = []
    prev_code = 0

    for i in range(len(childrens)):
        tag = childrens[i].tag
        html_ = tostring(childrens[i], encoding="utf-8").decode("utf-8")

        code = childrens[i].xpath("div/pre/code/text()")
        class_ = childrens[i].get("class")

        if len(code) != 0:
            solutions.append(
                {
                    "solution_id": f"{problemcode}[{prev_code}]",
                    "solution": code[0],
                }
            )
            prev_code += 1

        elif "problemTutorial" in html_:
            prev_code = 0
            problemcode = childrens[i].get("problemcode")

            if class_ == "spoiler":
                problemcode = (
                    childrens[i].xpath("div/div")[0].get("problemcode")
                )

    return SolutionsArray(solutions)


def clean_contests(contests):
    res = []
    for contest in contests:
        if (
            contest <= last_contest
            and contest not in ISSUES
            and contest in TASKS
        ):
            res.append(contest)
    return res


def clean_tasks(tasks):
    res = []
    for task in tasks:
        task = task.upper()
        for i, char in enumerate(task):
            if not char.isdigit():
                if (
                    int(task[:i]) not in ISSUES
                    and int(task[:i]) <= last_contest
                    and task[i:] in [task[0] for task in TASKS[int(task[:i])]]
                ):
                    res.append([int(task[:i]), task[i:]])
                break
    return res


def get_tasks(contests):
    all_tasks = []
    for contest in contests:
        for task, _, _ in TASKS[contest]:
            all_tasks.append([contest, task])
    return all_tasks


TASKS, last_contest = problemset()
