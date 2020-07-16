import asyncio

import aiohttp
from lxml.etree import tostring
from lxml.html import fromstring

from .error import error
from .models import SolutionsArray

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


async def get_problemset():
    async with aiohttp.ClientSession() as session, session.get(
        "https://codeforces.com/api/problemset.problems?lang=ru"
    ) as response:
        if response.status == 200:
            return await response.json()
        else:
            error()


def problemset():
    data = asyncio.run(get_problemset())
    data = data["result"]["problems"]

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
    for key in tasks:
        tasks[key].sort()
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
        if "Tutorial" in material.text_content():
            material_link = material.get("href")
    if material_link is None:
        return None
    return material_link.split("/")[-1]


def get_codeforces_submition(html):
    xpath = '//*[@id="program-source-text"]'
    return fromstring(html).xpath(xpath)[0].text


def parse_link(url, html):
    if url.startswith("https://codeforces.com"):
        return get_codeforces_submition(html)
    elif url.startswith("https://pastebin.com/"):
        return html


def parse_blog(tree):
    childrens = tree.xpath('//*[@id="pageContent"]/div/div/div/div[3]/div')[
        0
    ].getchildren()
    solutions = []
    prev_code = 0
    problemcode = None

    urls = {}

    for i in range(len(childrens)):
        html_ = tostring(childrens[i], encoding="utf-8").decode("utf-8")
        code = childrens[i].xpath("div/pre/code/text()")
        codeforces_submission_href = childrens[i].get("href")

        if codeforces_submission_href is None:
            links = childrens[i].xpath("a")

            for link in links:
                href = link.get("href")
                if "submission" in href or "pastebin" in href:
                    codeforces_submission_href = href
                    # TODO 2 CF links
                    break

        elif (
            "submission" not in codeforces_submission_href
            and "pastebin" not in codeforces_submission_href
        ):
            codeforces_submission_href = None
        if problemcode is not None and codeforces_submission_href is not None:
            if problemcode not in urls:
                urls[problemcode] = [codeforces_submission_href]
            else:
                urls[problemcode].append(codeforces_submission_href)

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
    return SolutionsArray(solutions, urls)


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


def html_print(tree):
    if type(tree) == str:
        tree = fromstring(tree)
    return tostring(tree, encoding="utf-8", pretty_print=True).decode("utf-8")


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


__all__ = [
    "ISSUES",
    "OLD_ISSUES",
    "clean_contests",
    "clean_tasks",
    "get_codeforces_submition",
    "get_condition",
    "get_contest_title",
    "get_problemset",
    "get_tasks",
    "html_print",
    "materials",
    "parse_blog",
    "parse_link",
    "problemset",
]
