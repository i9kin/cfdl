"""aio.py
============
Module for fast and asynchronous requests to the server to get information.

Because of this, maximum performance is achieved

use aiohttp(asyncio requests) + ThreadPoolExecutor(pool of threads)

https://ru.stackoverflow.com/questions/899584/async-i-o-multithreading-cpu-%d0%9f%d0%b0%d1%80%d1%81%d0%b8%d0%bd%d0%b3-python
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import aiohttp
from lxml.html import HtmlElement, fromstring
from magic import from_buffer as file_type

from cfdl.bar_utils import Bar
from cfdl.models import Data
from cfdl.utils import (extend_task, get_tasks, get_tutorials, parse_tutorial,
                        rewrite_link, tasks_jsonify)
from cfdl.xhr import xhr_tutorials

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
}

# https://stackoverflow.com/questions/59902102/why-is-imperative-mood-important-for-docstrings
# https://stackoverflow.com/questions/3898572/what-is-the-standard-python-docstring-format


def get_tree(
    html: str,
) -> HtmlElement:
    """Get HtmlElement from a html.

    Args:
        html (str): html page content

    Returns:
        HtmlElement : tree element
    """
    tree = fromstring(html)
    tree.rewrite_links(rewrite_link)
    return tree


async def contests_html(
    session: aiohttp.ClientSession,
    page: int,
) -> str:
    """Get html of a contest page.

    Args:
        session (aiohttp.ClientSession) : session
        page (int) : number of page (0..)

    Returns:
        Html of page.
    """
    url = "https://codeforces.com/contests/page/{0}?complete=true".format(
        page,
    )
    async with session.get(url) as response:
        return await response.text()


def get_contest_from_page(tree: HtmlElement) -> List[Tuple[str, int]]:
    """Get list of tasks from tree.

    Args:
        tree (HtmlElement) : tree of contest page.

    Returns:
        List[Tuple[str, int]] : contest_name, contest_id
    """
    contests = []
    table = tree.xpath(
        '//*[@id="pageContent"]/div[1]/div[2]/div[1]/div[6]/table/tr',
    )[1:]
    for contest in table:
        text = contest.text_content().split()
        contest_name = " ".join(text[: text.index("Enter")])
        contest_id = contest.get("data-contestid")
        if contest_id == "693":
            continue
        contests.append((contest_name, int(contest_id)))
    return contests


async def get_html_blog(
    session: aiohttp.ClientSession,
    url: str,
    contests: List[int],
) -> Tuple[str, str, List[int]]:
    """Get html from a blog url.

     Args:
        session (aiohttp.ClientSession) : session
        url (str) : blog url
        contests (List[int]) : list of contests

    Returns:
        Tuple[str, str, List[int]] : url, html, contests list
    """
    async with session.get(url) as resp:
        return url, await resp.text(), contests


async def get_html_task(
    session: aiohttp.ClientSession,
    contest_id: int,
    task_letter: str,
) -> Tuple[int, str, str]:
    """Get html of condition from a task.

    Args:
        session (aiohttp.ClientSession) : session
        contest_id (int) : contest id of the contest
        task_letter (str) : letter of the task

    Returns:
        Tuple[int, str, str] : contest_id, task_letter, html code of the task.
    """
    url = "https://codeforces.com/contest/{0}/problem/{1}?locale=ru".format(
        contest_id,
        task_letter,
    )
    async with session.get(url) as resp:
        text = await resp.text(errors="ignore")
        if file_type(text, mime=True) != "text/html":
            return contest_id, task_letter, "<head></head><body></body>"
        return contest_id, task_letter, text


async def get_html_contest(
    session: aiohttp.ClientSession,
    contest_id: int,
) -> Tuple[int, str]:
    """Get html of the contest main page.

    Args:
        session (aiohttp.ClientSession) : session
        contest_id (int) : contest id of the contest

    Returns:
        Tuple[int, str] : contest_id, html code of the contest.
    """
    url = "http://codeforces.com/contest/{contest_id}?locale=ru".format(
        contest_id=contest_id,
    )
    async with session.get(url) as resp:
        return contest_id, await resp.text()


async def parse_contest(
    session: aiohttp.ClientSession,
    contests: List[int],
    debug: bool = True,
) -> List[Tuple[int, str]]:
    """Get url for all tutorials and extends tasks for the contests.

    Args:
        session (aiohttp.ClientSession) : session
        contests (List[int]) : list of contests
        debug (bool) : if true shows progress bar

    Returns:
        List[Tuple[int, str]] : contest_id, tutorial url for this contest_id.
    """
    loop = asyncio.get_running_loop()

    progress_bar = Bar(range(len(contests)), debug=debug)
    contests_tree = []

    futeres = [get_html_contest(session, url) for url in contests]

    with ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(futeres):
            contest_id, contest_html = await future

            contest_tree = await loop.run_in_executor(
                pool,
                get_tree,
                contest_html,
            )

            contests_tree.append((contest_id, contest_tree))

            progress_bar.update()
            progress_bar.set_description(
                "parse contest {0}".format(
                    contest_id,
                ),
            )

    blog_urls = []
    for contest_id, contest_tree in contests_tree:
        extend_task(contest_id, contest_tree)
        for url in get_tutorials(contest_tree):
            blog_urls.append((contest_id, url))
    return blog_urls


async def parse_blog(
    session: aiohttp.ClientSession,
    data_storage: Data,
    blog_urls: dict,
    debug: bool = True,
):
    """Extract solutions for all tasks in this tutorials.

    Args:
        session (aiohttp.ClientSession) : session
        data_storage (Data) : data object
        blog_urls (dict) : list of contests
        debug (bool) : if true shows progress bar
    """
    loop = asyncio.get_running_loop()
    progress_bar = Bar(range(len(blog_urls)), debug=debug)

    futeres = [
        get_html_blog(session, url, blog_urls[url]) for url in blog_urls
    ]

    with ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(futeres):
            url, html, contests = await future

            await loop.run_in_executor(
                pool,
                parse_tutorial,
                html,
                data_storage,
                contests,
                url,
            )

            progress_bar.update()
            progress_bar.set_description("parse blog")


async def parse_tasks(
    session: aiohttp.ClientSession,
    problems: List[Tuple[int, str]],
    debug: bool = True,
) -> List[Tuple[int, str, HtmlElement]]:
    """Get html tree for the tasks.

    Args:
        session (aiohttp.ClientSession) : session
        problems (List[Tuple[int, str]]) : list of tuple (contest_id, task_letter)
        debug (bool) : if true shows progress bar

    Returns:
        List[Tuple[int, str, HtmlElement]] : contest_id, task_letter, tree for task
    """
    loop = asyncio.get_running_loop()
    tasks = []
    progress_bar = Bar(range(len(problems)), debug=debug)

    futeres = [
        get_html_task(session, contest_id, task_letter)
        for contest_id, task_letter in problems
    ]

    with ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(futeres):
            contest_id, task_letter, task_html = await future

            task_tree = await loop.run_in_executor(pool, get_tree, task_html)

            progress_bar.update()
            progress_bar.set_description(
                "parse task {0}{1}".format(
                    contest_id,
                    task_letter,
                ),
            )

            tasks.append((contest_id, task_letter, task_tree))
    return tasks


async def async_parse(
    data_storage: Data,
    contests: List[int],
    debug: bool = True,
):
    """Parse contests. Save all data in data_storage.

    Args:
        data_storage (Data) : data object
        contests (List[int]) : list of contests
        debug (bool) : if true shows progress bar
    """
    session = aiohttp.ClientSession()

    all_contests = list(set(contests))

    blogs = await parse_contest(
        session=session,
        contests=all_contests,
        debug=debug,
    )

    blog_urls = {}
    for contest_id, url in blogs:
        if url not in blog_urls:
            blog_urls[url] = [contest_id]
        elif contest_id not in blog_urls[url]:
            blog_urls[url].append(contest_id)

    all_tasks = get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]
    for tutorial in await xhr_tutorials(all_tasks=all_tasks, debug=debug):
        data_storage.add_xhr_data(tutorial)
    await parse_blog(
        session=session,
        blog_urls=blog_urls,
        debug=debug,
        data_storage=data_storage,
    )

    all_tasks = get_tasks(contests)

    for contest_id, letter, tree in await parse_tasks(
        session=session,
        problems=all_tasks,
        debug=debug,
    ):
        data_storage.add_task_tree(
            contest_id=contest_id,
            letter=letter,
            tree=tree,
        )
    await session.close()


async def async_get_contest(debug: bool = True) -> List[Tuple[str, int]]:
    """Get all contests from codeforces.

    Args:
        debug (bool) : if true shows progress bar

    Returns:
        List[Tuple[str, int]] : contest_name, contest_id
    """
    session = aiohttp.ClientSession()
    tree = get_tree(await contests_html(session=session, page=1))

    cnt_pages = int(
        tree.xpath('//*[@id="pageContent"]/div[1]/div[2]/div[2]/ul/li')[-2]
        .text_content()
        .strip()
    )

    contests = [*get_contest_from_page(tree)]

    loop = asyncio.get_running_loop()
    progress_bar = Bar(range(cnt_pages), debug=debug)
    progress_bar.update()
    progress_bar.set_description("parse contests page")

    futeres = [
        contests_html(session=session, page=page)
        for page in range(2, cnt_pages + 1)
    ]

    with ThreadPoolExecutor() as pool:
        for future in asyncio.as_completed(futeres):
            html = await future
            tree = await loop.run_in_executor(pool, get_tree, html)
            contests += get_contest_from_page(tree)
            progress_bar.update()
    await session.close()
    contests.sort(key=lambda element: element[1])
    return contests


def get_contests(debug: bool = True) -> List[Tuple[str, int]]:
    """Execute async function

    Args:
        debug (bool) : if true shows progress bar.

    Returns:
        List[Tuple[str, int]] : contest_name, contest_id
    """
    return asyncio.run(async_get_contest(debug=debug))


def download(data_storage: Data, contests: List[int], debug=True):
    """Run contests parsing. Save data to database.

    Args:
        data_storage (Data) : data object
        contests (List[int]) : list of contests
        debug (bool) : if true shows progress bar.
    """
    asyncio.run(
        async_parse(
            data_storage=data_storage,
            contests=contests,
            debug=debug,
        ),
    )
    for task in tasks_jsonify(data=data_storage, tasks=get_tasks(contests)):
        data_storage.add_json_task(task)


__all__ = [
    "async_get_contest",
    "async_parse",
    "contests_html",
    "download",
    "get_contest_from_page",
    "get_contests",
    "get_html_blog",
    "get_html_contest",
    "get_html_task",
    "get_tree",
    "headers",
    "parse_blog",
    "parse_contest",
    "parse_tasks",
]
