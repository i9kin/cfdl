# https://ru.stackoverflow.com/questions/899584/async-i-o-multithreading-cpu-%d0%9f%d0%b0%d1%80%d1%81%d0%b8%d0%bd%d0%b3-python
import asyncio
import concurrent.futures

import aiohttp
from lxml.html import fromstring
from tqdm import tqdm

from .utils import materials, parse_blog, problemset


async def get_html_contest(contest_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://codeforces.com/contest/{contest_id}?locale=ru"
        ) as resp:
            return contest_id, await resp.text()


async def get_html_task(contest_id, task_letter):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://codeforces.com/problemset/problem/{contest_id}/{task_letter}?locale=ru"
        ) as resp:
            return contest_id, task_letter, await resp.text()


def get_materials(contest_html):
    # получение url разбора для контеста
    material_url = materials(fromstring(contest_html))
    if material_url is None:
        return None
    return f"https://codeforces.com/blog/entry/{material_url}?locale=ru"


class AIO:
    def __init__(self, last_contest):
        # last_contest - 1367
        self.contests_task = [{} for i in range(last_contest + 1)]
        self.contests_blog = [[] for i in range(last_contest + 1)]

    def append_task(self, contest_id, task_letter, tree):
        self.contests_task[contest_id][task_letter] = tree

    def get_task(self, contest_id, task_letter):
        return self.contests_task[contest_id][task_letter]

    def append_blog(self, contest_id, solutions):
        self.contests_blog[contest_id] = solutions

    def get_blog(self, contest_id):
        return self.contests_blog[contest_id]


def get_tree(html):
    # получение lxml.tree  для url
    return fromstring(html)


def parse_blog_from_html(html):
    # получение lxml.tree  для url
    return parse_blog(fromstring(html))


async def get_html_blog(contest_id, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return contest_id, await resp.text()


# contests, taksks


def parse(contests, tasks):
    return asyncio.run(build(contests))


async def parse_blog_urls(contests):
    loop = asyncio.get_running_loop()
    blog_urls = []

    ECTRACT_BLOG_URL_BAR = tqdm(
        range(len(contests)),
        ascii=" ━",
        bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
    )
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [get_html_contest(url) for url in contests]
        ):
            contest_id, contest_html = await future
            material_url = await loop.run_in_executor(
                pool, get_materials, contest_html
            )
            ECTRACT_BLOG_URL_BAR.update()
            ECTRACT_BLOG_URL_BAR.set_description(
                "extracting blog url for contest %s" % contest_id
            )
            if material_url is not None:
                blog_urls.append((contest_id, material_url))
    return blog_urls


async def parse_blogs(blog_urls):
    # appending blog.tree for contest
    loop = asyncio.get_running_loop()
    blogs = []

    PARSE_BLOGS_BAR = tqdm(
        range(len(blog_urls)),
        ascii=" ━",
        bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
    )
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [get_html_blog(contest_id, url) for contest_id, url in blog_urls]
        ):
            contest_id, html = await future
            solutions = await loop.run_in_executor(
                pool, parse_blog_from_html, html
            )
            PARSE_BLOGS_BAR.update()
            PARSE_BLOGS_BAR.set_description(
                "parse blog for contest %s" % contest_id
            )
            blogs.append((contest_id, solutions))
    return blogs


async def parse_tasks(problems):
    loop = asyncio.get_running_loop()
    tasks = []

    PARSE_TASKS_BAR = tqdm(
        range(len(problems)),
        ascii=" ━",
        bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
    )

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [
                get_html_task(contest_id, contest_leter)
                for contest_id, contest_leter in problems
            ]
        ):
            contest_id, task_letter, task_html = await future
            task_tree = await loop.run_in_executor(pool, get_tree, task_html)
            PARSE_TASKS_BAR.update()
            PARSE_TASKS_BAR.set_description(
                f"parse task {contest_id}{task_letter}"
            )
            tasks.append((contest_id, task_letter, task_tree))
    return tasks


async def build(contests):
    loop = asyncio.get_running_loop()
    tasks, last_contest = problemset()

    blog_urls = await parse_blog_urls(contests)
    blogs = await parse_blogs(blog_urls)

    a = AIO(last_contest)

    for blog in blogs:
        a.append_blog(*blog)

    problems = []
    for contest in contests:
        for problem, _, _ in tasks[contest]:
            problems.append([contest, problem])
    tasks = await parse_tasks(problems)
    for task in tasks:
        a.append_task(*task)
    return a
