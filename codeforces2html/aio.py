# https://ru.stackoverflow.com/questions/899584/async-i-o-multithreading-cpu-%d0%9f%d0%b0%d1%80%d1%81%d0%b8%d0%bd%d0%b3-python
import asyncio
import concurrent.futures
from typing import Tuple, Union

import aiohttp
from lxml.html import HtmlElement, fromstring

from .bar_urils import Bar
from .models import SolutionsArray
from .utils import materials, parse_blog, problemset


class AIO:
    """class for saving data"""

    def __init__(self, last_contest: int) -> None:
        self.contests_task = [{} for i in range(last_contest + 1)]
        self.contests_blog = [None for i in range(last_contest + 1)]

    def append_task(
        self, contest_id: int, task_letter: str, tree: HtmlElement
    ) -> None:
        """
        :param contest_id: id of the contest
        :param task_letter: letter of the task
        :param tree: class lxml.html.HtmlElement of task
        """
        self.contests_task[contest_id][task_letter] = tree

    def append_blog(self, contest_id: int, solutions: SolutionsArray) -> None:
        """
        :param contest_id: int
        :param solutions: class of code solutions from current contest blog
        """
        self.contests_blog[contest_id] = solutions

    def get_task(self, contest_id: int, task_letter: str) -> HtmlElement:
        """
        :param contest_id: id of the contest
        :param task_letter: letter of the task
        :return: class lxml.html.HtmlElement of task
        """
        return self.contests_task[contest_id][task_letter]

    def get_blog(self, contest_id: int) -> SolutionsArray:
        """
        :param contest_id: id of the contest
        :return: class of code solutions from current contest blog
        """
        return self.contests_blog[contest_id]


def get_materials(contest_html: str) -> Union[str, None]:
    """getting the url tutorial for the contest

    :param contest_html: html code of the contest
    :return: url tutorial or None
    """
    material_url = materials(fromstring(contest_html))
    if material_url is None:
        return None
    return f"https://codeforces.com/blog/entry/{material_url}?locale=ru"


def get_tree(html: str) -> HtmlElement:
    """getting the lxml.html.HtmlElement for a url"""
    return fromstring(html)


def parse_blog_from_html(html: str) -> SolutionsArray:
    """getting class of code solutions from html (tutorial)"""
    return parse_blog(fromstring(html))


async def get_html_contest(contest_id: int) -> Tuple[int, str]:
    """getting the html code of the contest

    :param contest_id: id of the contest
    :return: tuple of contest_id and html code of the contest
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://codeforces.com/contest/{contest_id}?locale=ru"
        ) as resp:
            return contest_id, await resp.text()


async def get_html_task(
    contest_id: int, task_letter: str
) -> Tuple[int, str, str]:
    """getting the html code of the task

    :param contest_id: id of the contest
    :param task_letter: letter of the task
    :return: tuple of contest_id, task_letter and html code of the task
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://codeforces.com/problemset/problem/{contest_id}/{task_letter}?locale=ru"
        ) as resp:
            return contest_id, task_letter, await resp.text()


async def get_html_blog(contest_id: int, url: str) -> Tuple[int, str]:
    """getting the html code of the solution

    :param contest_id: id of the contest
    :param url: of the tutorial
    :return: tuple of contest_id, html code of the tutorial
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return contest_id, await resp.text()


async def parse_blog_urls(contests, debug=True):
    loop = asyncio.get_running_loop()
    blog_urls = []
    bar = Bar(range(len(contests)), debug=debug)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [get_html_contest(url) for url in contests]
        ):
            contest_id, contest_html = await future
            material_url = await loop.run_in_executor(
                pool, get_materials, contest_html
            )

            bar.update()
            bar.set_description("parse contest %s" % contest_id)

            if material_url is not None:
                blog_urls.append((contest_id, material_url))
    return blog_urls


async def parse_blogs(blog_urls, debug=True):
    # appending blog.tree for contest
    loop = asyncio.get_running_loop()
    blogs = []

    bar = Bar(range(len(blog_urls)), debug=debug)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [get_html_blog(contest_id, url) for contest_id, url in blog_urls]
        ):
            contest_id, html = await future
            solutions = await loop.run_in_executor(
                pool, parse_blog_from_html, html
            )
            bar.update()
            bar.set_description("parse blog %s " % contest_id)
            blogs.append((contest_id, solutions))
    return blogs


async def parse_tasks(problems, debug=True):
    loop = asyncio.get_running_loop()
    tasks = []
    bar = Bar(range(len(problems)), debug=debug)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [
                get_html_task(contest_id, contest_leter)
                for contest_id, contest_leter in problems
            ]
        ):
            contest_id, task_letter, task_html = await future
            task_tree = await loop.run_in_executor(pool, get_tree, task_html)

            bar.update()
            bar.set_description(f"parse task {contest_id}{task_letter}")
            tasks.append((contest_id, task_letter, task_tree))
    return tasks


async def async_parse(contests, additional_tasks, debug=True):
    tasks, last_contest = problemset()

    contests += [task[0] for task in additional_tasks]

    blog_urls = await parse_blog_urls(contests, debug)
    blogs = await parse_blogs(blog_urls, debug)

    a = AIO(last_contest)

    for blog in blogs:
        a.append_blog(*blog)

    all_tasks = additional_tasks.copy()
    for contest in contests:
        for task, _, _ in tasks[contest]:
            all_tasks.append([contest, task])

    tasks = await parse_tasks(all_tasks, debug)
    for task in tasks:
        a.append_task(*task)
    return a


def parse(contests, tasks, debug=True):
    return asyncio.run(async_parse(contests.copy(), tasks, debug))
