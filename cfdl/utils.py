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


PROBLEMSET = None
NAME = None


def get_task(name, my_contest_id):
    """div1/2 contest"""
    contest_id = -1
    indx = -1
    for cur_contest_id, ind in NAME[name]:
        if abs(cur_contest_id - my_contest_id) < abs(
            contest_id - my_contest_id
        ):
            contest_id = cur_contest_id
            indx = ind
    return contest_id, indx


def contests(name, my_contest_id):
    """div1/div2 fix return [div_1, div2] or [divX] like [(contest_id, indx), ...]"""
    contests = []
    for contest_id, indx in NAME[name]:
        if abs(contest_id - my_contest_id) < 4:
            contests.append((contest_id, indx))
    return contests


def extend_problemset(contest_id, letter, name, number):
    global PROBLEMSET
    for _, task_name, _ in PROBLEMSET[0][contest_id]:
        if task_name == name:
            return
    print(contest_id, name)

    copy_contest_id, indx = get_task(name, contest_id)
    task = PROBLEMSET[0][copy_contest_id][indx].copy()
    task[0] = letter
    if contest_id not in PROBLEMSET[0]:
        PROBLEMSET[0][contest_id] = [task]
    else:
        PROBLEMSET[0][contest_id].append(task)

    NAME[name].append((contest_id, number))


def extend_task(id, tree):
    """Extend tasks like div1 div2 but api send div1"""
    tasks_xpath = '//*[@id="pageContent"]/div[2]/div[6]/table/tr'
    for i, task in enumerate(tree.xpath(tasks_xpath)[1:]):
        letter = task.xpath("td[1]/a")[0].text_content().strip()
        name = " ".join(
            task.xpath("td[2]/div/div[1]/a")[0].text_content().split()
        )
        extend_problemset(id, letter, name, i)


def problemset():
    global PROBLEMSET, NAME
    if PROBLEMSET is not None:
        return PROBLEMSET
    data = asyncio.run(get_problemset())
    data = data["result"]["problems"]
    last_contest = data[0]["contestId"]
    tasks = {}
    NAME = {}
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
            if task[1] not in NAME:
                NAME[task[1]] = [(contest_id, i)]
            else:
                NAME[task[1]].append((contest_id, i))
    for name in NAME:
        NAME[name].sort()

    PROBLEMSET = tasks, last_contest
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
            link = material.get("href")
            if link not in invalid_blogs and link.startswith("/blog/entry/"):
                material_link = link
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
    urls = {}

    for element in childrens:
        problemTutorial = element.find_class("problemTutorial")
        if len(problemTutorial) != 0:
            problemTutorial[0].text = "CF_API!!!!!!!!!!!!!!!!!"
            problemcode = problemTutorial[0].attrib["problemcode"]
            name = get_task_name(problemcode)
            print(name, contests(name, int(get_contest(problemcode))))

    return SolutionsArray(solutions, urls)


def get_task_name(problemcode: str):
    contest = int(get_contest(problemcode))
    letter = get_letter(problemcode)
    for task in PROBLEMSET[0][contest]:
        if task[0] == letter:
            return task[1]
    exit(-1)


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
