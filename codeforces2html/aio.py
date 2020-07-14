# https://ru.stackoverflow.com/questions/899584/async-i-o-multithreading-cpu-%d0%9f%d0%b0%d1%80%d1%81%d0%b8%d0%bd%d0%b3-python
"""aio.py
============
Module for fast and asynchronous requests to the server to get information.

Because of this, maximum performance is achieved

use aiohttp(asyncio requests) + ThreadPoolExecutor(pool of threads)
"""
import asyncio
import concurrent.futures
from typing import List, Tuple, Union

import aiohttp
from lxml.html import HtmlElement, fromstring

from .bar_urils import Bar
from .models import SolutionsArray
from .utils import get_tasks, last_contest, materials, parse_blog, parse_link

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
}


class AIO:
    """class for saving data."""

    def __init__(self, last_contest: int) -> None:
        self.contests_task = [{} for _ in range(last_contest + 1)]
        self.contests_blog = [[] for _ in range(last_contest + 1)]

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
    """getting the url tutorial for the contest.

    :param contest_html: html code of the contest
    :return: url tutorial or None
    """
    material_url = materials(fromstring(contest_html))
    if material_url is None:
        return None
    return f"https://codeforces.com/blog/entry/{material_url}?locale=ru"


def get_tree(html: str) -> HtmlElement:
    """getting the lxml.html.HtmlElement for a url."""
    return fromstring(html)


def parse_blog_from_html(html: str) -> SolutionsArray:
    """getting class of code solutions from html (tutorial)"""
    return parse_blog(fromstring(html))


async def get_html_task(
    session: aiohttp.ClientSession, contest_id: int, task_letter: str
) -> Tuple[int, str, str]:
    """getting condition (the html code) of the task.

    :param session: aiohttp.ClientSession
    :param contest_id: id of the contest
    :param task_letter: letter of the task
    :return: tuple of contest_id, task_letter and html code of the task
    """

    async with session.get(
        f"http://codeforces.com/problemset/problem/{contest_id}/{task_letter}?locale=ru"
    ) as resp:
        return contest_id, task_letter, await resp.text()


async def get_html_blog(
    session: aiohttp.ClientSession, contest_id: int, url: str
) -> Tuple[int, str]:
    """getting the html code of the blog.

    :param session: aiohttp.ClientSession
    :param contest_id: id of the contest
    :param url: of the tutorial
    :return: tuple of contest_id, html code of the blog
    """
    async with session.get(url) as resp:
        return contest_id, await resp.text()


async def get_html_contest(
    session: aiohttp.ClientSession, contest_id: int
) -> Tuple[int, str]:
    """getting the html code of the contest.

    :param session: aiohttp.ClientSession
    :param contest_id: id of the contest
    :return: tuple of contest_id and html code of the contest
    """

    async with session.get(
        f"http://codeforces.com/contest/{contest_id}?locale=ru"
    ) as resp:
        return contest_id, await resp.text()


async def parse_blog_urls(
    session: aiohttp.ClientSession, contests: List[int], debug: bool = True
) -> List[Tuple[int, str]]:
    """getting the url of the blog (tutorial) for the contests.

    :param session: aiohttp.ClientSession
    :param contests: [contest_id, ...]
    :param debug: if true show bar
    :return: list of tuple(contest_id, url of the blog (tutorial) for the contest)
    """
    loop = asyncio.get_running_loop()
    blog_urls = []
    bar = Bar(range(len(contests)), debug=debug)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [get_html_contest(session, url) for url in contests]
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


async def parse_blogs(
    session: aiohttp.ClientSession,
    blog_urls: List[Tuple[int, str]],
    debug: bool = True,
) -> List[Tuple[int, SolutionsArray]]:
    """getting the solutions from the the blog (tutorial) for the contests.

    :param session: aiohttp.ClientSession
    :param blog_urls: [(contest_id, url_blog for this contest), .....]
    :param debug: if true show bar
    :return: list of tuple(contest_id, solutions for this contest)
    """
    loop = asyncio.get_running_loop()
    blogs = []

    bar = Bar(range(len(blog_urls)), debug=debug)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [
                get_html_blog(session, contest_id, url)
                for contest_id, url in blog_urls
            ]
        ):
            contest_id, html = await future
            solutions = await loop.run_in_executor(
                pool, parse_blog_from_html, html
            )
            bar.update()
            bar.set_description("parse blog %s " % contest_id)
            blogs.append((contest_id, solutions))
    return blogs


async def parse_tasks(
    session: aiohttp.ClientSession,
    problems: List[Tuple[int, str]],
    debug: bool = True,
) -> List[Tuple[int, str, HtmlElement]]:
    """getting the condition of the tasks.

    :param session: aiohttp.ClientSession
    :param problems: [(contest_id, task_letter), ....]
    :param debug: if true show bar
    :return: [(contest_id, task_letter, HtmlElement), ...]
    """
    loop = asyncio.get_running_loop()
    tasks = []
    bar = Bar(range(len(problems)), debug=debug)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [
                get_html_task(session, contest_id, contest_leter)
                for contest_id, contest_leter in problems
            ]
        ):
            contest_id, task_letter, task_html = await future
            task_tree = await loop.run_in_executor(pool, get_tree, task_html)

            bar.update()
            bar.set_description(f"parse task {contest_id}{task_letter}")
            tasks.append((contest_id, task_letter, task_tree))

    return tasks


async def get_html(session, i, problemcode, url: str):
    async with session.get(url) as resp:
        return i, problemcode, url, await resp.text()


async def parse_url_blogs(
    session: aiohttp.ClientSession,
    blogs: List[Tuple[int, SolutionsArray]],
    debug: bool = True,
) -> List[Tuple[int, SolutionsArray]]:
    """getting the solutions from the links in the blog (tutorial) for the
    contests like link (/contest/1372/submission/86603896, (pastebin TODO))

    :param session: aiohttp.ClientSession
    :param blogs: [(contest_id, SolutionsArray), .....]
    :param debug: if true show bar
    :return: list of tuple(contest_id, solutions for this contest)
    """
    urls = []
    for i, (contest_id, solution_array) in enumerate(blogs):
        for problemcode in solution_array.urls:
            for url in solution_array.urls[problemcode]:
                if not url.startswith("http"):
                    url = "https://codeforces.com" + url
                elif url.startswith("https://pastebin.com/"):
                    url = url[:21] + "raw" + "/" + url[21:]
                urls.append((i, problemcode, url))

    loop = asyncio.get_running_loop()
    bar = Bar(range(len(urls)), debug=debug)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [
                get_html(session, i, problemcode, url)
                for i, problemcode, url in urls
            ]
        ):
            i, problemcode, url, html = await future
            submition = await loop.run_in_executor(pool, parse_link, url, html)
            blogs[i][1].update(problemcode, submition)

            bar.update()
            bar.set_description(f"parse {problemcode}")


async def async_parse(
    contests: List[int],
    additional_tasks: List[Tuple[int, str]],
    RCPC: str,
    debug: bool = True,
) -> AIO:
    """getting and adding all information for the contests and tasks.

    :param contests: [contest_id, ...]
    :param additional_tasks: [(contest_id, task_letter), ....]
    :param RCPC rsa decrypt (js)
    :param debug: if true show bar
    :return: AIO class
    """
    session = aiohttp.ClientSession(cookies={"RCPC": RCPC})

    all_contests = contests + [task[0] for task in additional_tasks]
    all_contests = list(set(all_contests))

    blog_urls = await parse_blog_urls(session, all_contests, debug)
    blogs = await parse_blogs(session, blog_urls, debug)

    await parse_url_blogs(session, blogs, debug)

    a = AIO(last_contest)

    for blog in blogs:
        a.append_blog(*blog)

    all_tasks = additional_tasks.copy() + get_tasks(contests)
    tasks = await parse_tasks(session, all_tasks, debug)
    for task in tasks:
        a.append_task(*task)

    await session.close()
    return a


def parse(
    contests: List[int],
    additional_tasks: List[Tuple[int, str]],
    RCPC: str,
    debug: bool = True,
) -> AIO:
    """run async function async_parse.

    :param contests: [contest_id, ...]
    :param additional_tasks: [(contest_id, task_letter), ....]
    :param RCPC rsa decrypt (js)
    :param debug: if true show bar
    :return: AIO class
    """
    return asyncio.run(async_parse(contests, additional_tasks, RCPC, debug))


__all__ = [
    "AIO",
    "async_parse",
    "get_html",
    "get_html_blog",
    "get_html_contest",
    "get_html_task",
    "get_materials",
    "get_tree",
    "headers",
    "parse",
    "parse_blog_from_html",
    "parse_blog_urls",
    "parse_blogs",
    "parse_tasks",
    "parse_url_blogs",
]
