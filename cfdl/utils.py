import html
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


lru_problemset = None
lru_name = None


def extend_problemset(contest_id, letter, name):
    global lru_problemset
    for _, task_name, _ in lru_problemset[0][contest_id]:
        if task_name == name:
            return
    copy_contest_id = -1
    ind_ = -1
    for cur_contest_id, ind in lru_name[name]:
        if abs(cur_contest_id - contest_id) < abs(
            copy_contest_id - contest_id
        ):
            copy_contest_id = cur_contest_id
            ind_ = ind
    task = lru_problemset[0][copy_contest_id][ind_].copy()
    task[0] = letter
    if contest_id not in lru_problemset[0]:
        lru_problemset[0][contest_id] = [task]
    else:
        lru_problemset[0][contest_id].append(task)


def extend_task(id, tree):
    """Extend tasks like div1 div2 but api send div1"""
    tasks_xpath = '//*[@id="pageContent"]/div[2]/div[6]/table/tr'
    for task in tree.xpath(tasks_xpath)[1:]:
        letter = task.xpath("td[1]/a")[0].text_content().strip()
        name = " ".join(
            task.xpath("td[2]/div/div[1]/a")[0].text_content().split()
        )
        extend_problemset(id, letter, name)


def problemset():
    global lru_problemset, lru_name
    if lru_problemset is not None:
        return lru_problemset
    data = asyncio.run(get_problemset())
    data = data["result"]["problems"]
    last_contest = data[0]["contestId"]
    tasks = {}
    lru_name = {}
    for task in data:
        contest_id = task["contestId"]
        letter = task["index"]
        tags = task["tags"]
        name = task["name"]
        if contest_id not in tasks:
            tasks[contest_id] = [[letter, name, tags]]
        else:
            tasks[contest_id].append([letter, name, tags])
    for contest_id in tasks:
        tasks[contest_id].sort()
    for contest_id in tasks:
        for i, task in enumerate(tasks[contest_id]):
            if task[1] not in lru_name:
                lru_name[task[1]] = [(contest_id, i)]
            else:
                lru_name[task[1]].append((contest_id, i))
    for name in lru_name:
        lru_name[name].sort()

    lru_problemset = tasks, last_contest
    return tasks, last_contest


def get_condition(tree):
    task_element = tree.xpath('//*[@id="pageContent"]/div[2]')[0]
    return tostring(task_element, encoding="utf-8").decode("utf-8")


def get_contest_title(tree):
    contest_xpath1 = '//*[@id="sidebar"]/div[1]/table/tbody/tr[1]/th/a'
    contest_xpath2 = '//*[@id="sidebar"]/div[2]/table/tbody/tr[1]/th/a'  # 2
    element = tree.xpath(contest_xpath1)
    if element == []:
        element = tree.xpath(contest_xpath2)
    return element[0].text_content()


def materials(tree):
    materials_xpath = '//*[@id="sidebar"]/div[4]/ul/li/span[1]/a'
    materials = tree.xpath(materials_xpath)
    if len(materials) == 0:
        materials_xpath = '//*[@id="sidebar"]/div[5]/ul/li/span[1]/a'
        materials = tree.xpath(materials_xpath)
    material_link = None
    # TODO araay

    invalid_blogs = [
        "/blog/entry/3770",
        "/blog/entry/419",
        "/blog/entry/3874",  # why?
    ]

    for material in materials:
        if "Разбор задач" in material.text_content():
            if material.get("href") not in invalid_blogs:
                material_link = material.get("href")
    # print(material_link)
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
    TASKS, last_contest = problemset()
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
    return html.unescape(
        tostring(tree, encoding="utf-8", pretty_print=True).decode("utf-8")
    )


def clean_tasks(tasks):
    TASKS, last_contest = problemset()
    res = []
    for task in tasks:
        task = task.upper()
        for i, char in enumerate(task):
            if not char.isdigit():
                if (
                    int(task[:i]) not in ISSUES
                    and int(task[:i]) <= last_contest
                    and int(task[:i]) in TASKS
                    and task[i:] in [task[0] for task in TASKS[int(task[:i])]]
                ):
                    res.append([int(task[:i]), task[i:]])
                break
    return res


def get_tasks(contests):
    TASKS, last_contest = problemset()
    all_tasks = []
    for contest in contests:
        for task, _, _ in TASKS[contest]:
            all_tasks.append([contest, task])
    return all_tasks


def get_letter(task_name):
    for i, char in enumerate(task_name):
        if not char.isdigit():
            return task_name[i:]


def get_contest(task_name):
    for i, char in enumerate(task_name):
        if not char.isdigit():
            return task_name[:i]


def get_divison(contest_title):
    m = {
        "1": ["Div. 1", "Div.1", "Див. 1", "Див.1"],
        "2": ["Div. 2", "Div.2", "Див. 2", "Див.2"],
        "3": ["Div. 3", "Div.3", "Див. 3", "Див.3"],
        "4": ["Div. 4", "Div.4", "Див. 4", "Див.4"],
        "gl": ["Global Round", "Good Bye", "Hello", "Технокубок"],
    }
    for div in m:
        for string in m[div]:
            if string in contest_title:
                return div
    return "gl"


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
