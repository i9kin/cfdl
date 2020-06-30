import json

from lxml import html
from lxml.etree import tostring

from models import Solutions, SolutionsArray


def problemset():
    # 'https://codeforces.com/api/problemset.problems'
    data = json.load(open("problemset.txt", "r"))["result"]["problems"]

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
