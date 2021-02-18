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

from . import xhr
from .bar_utils import Bar
from .models import Data
from .utils import (
    extend_task,
    get_tasks,
    materials,
    parse_tutorial,
    problemset,
    tasks_jsonify,
)

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
}


def get_tree(html: str) -> HtmlElement:
    """getting the lxml.html.HtmlElement for a html"""
    return fromstring(html)


def get_materials(contest_tree: HtmlElement) -> Union[str, None]:
    """getting the url tutorial for the contest. Using utils.materials
    :param contest_html: html code of the contest
    :return: url tutorial or None
    """
    material_url = materials(contest_tree)
    if material_url is None:
        return None
    return f"https://codeforces.com/blog/entry/{material_url}?locale=ru"


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


async def parse_contest(
    session: aiohttp.ClientSession, contests: List[int], debug: bool = True
) -> List[Tuple[int, str]]:
    """getting the url of the blog (tutorial) for the contests and extend tasks.

    :param session: aiohttp.ClientSession
    :param contests: [contest_id, ...]
    :param debug: if true show bar
    :return: list of tuple(contest_id, url of the blog (tutorial) for the contest)
    """
    loop = asyncio.get_running_loop()

    bar = Bar(range(len(contests)), debug=debug)
    contests_tree = []
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(
            [get_html_contest(session, url) for url in contests]
        ):
            contest_id, contest_html = await future

            contest_tree = await loop.run_in_executor(
                pool, get_tree, contest_html
            )
            contests_tree.append((contest_id, contest_tree))

            bar.update()
            bar.set_description("parse contest %s" % contest_id)

    blog_urls = []
    for contest_id, contest_tree in contests_tree:
        material_url = get_materials(contest_tree)
        extend_task(contest_id, contest_tree)
        if material_url is not None:
            blog_urls.append((contest_id, material_url))
    return blog_urls


async def parse_blog(
    session: aiohttp.ClientSession,
    data,
    blog_urls: List[Tuple[int, str]],
    debug: bool = True,
):
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
                pool, parse_tutorial, html, data
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


async def async_parse(
    data, contests: List[int], additional_tasks, debug: bool = True
):
    session = aiohttp.ClientSession()

    all_contests = contests + [task[0] for task in additional_tasks]
    all_contests = list(set(all_contests))

    blog_urls = await parse_contest(
        session=session, contests=all_contests, debug=debug
    )
    all_tasks = additional_tasks.copy() + get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]
    for t in await xhr.xhr_tutorials(all_tasks=all_tasks, debug=debug):
        data.add_xhr_data(t)
    await parse_blog(
        session=session, blog_urls=blog_urls, debug=debug, data=data
    )
    all_tasks = additional_tasks.copy() + get_tasks(contests)
    for contest_id, letter, tree in await parse_tasks(
        session=session, problems=all_tasks, debug=debug
    ):
        data.add_task_tree(contest_id=contest_id, letter=letter, tree=tree)
    await session.close()


def download(data: Data, contests, additional_tasks, debug=True):
    asyncio.run(
        async_parse(
            data=data,
            contests=contests,
            additional_tasks=additional_tasks,
            debug=debug,
        )
    )

    TASKS, _ = problemset()

    for contest in contests:
        tasks = tasks_jsonify(data, contest, TASKS[contest])
        for task in tasks:
            data.add_json_task(task)


__all__ = [
    "async_parse",
    "download",
    "get_html_blog",
    "get_html_contest",
    "get_html_task",
    "get_materials",
    "get_tree",
    "headers",
    "parse_blog",
    "parse_contest",
    "parse_tasks",
]
