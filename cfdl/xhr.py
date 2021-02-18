import asyncio

import aiohttp
from lxml.html import fromstring

from .bar_utils import Bar

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
}


async def get_token(session):
    resp = await session.get("https://codeforces.com/profile/MiFaFaOvO")
    async with resp:
        return (
            fromstring(await resp.text())
            .xpath('//*[@id="body"]/div[3]/div[5]/form/input[1]')[0]
            .get("value")
        )


async def problemData(task, session, csrf_token):
    resp = await session.post(
        "https://codeforces.com/data/problemTutorial?locale=ru",
        data={
            "problemCode": task,
            "csrf_token": csrf_token,
        },
        headers={
            "x-requested-with": "XMLHttpRequest",
            "x-csrf-token": csrf_token,
        },
    )
    async with resp:
        return task, await resp.json()


async def xhr_tutorials(all_tasks, debug):
    session = aiohttp.ClientSession(headers=headers)
    csrf_token = await get_token(session)
    tutorials = []
    bar = Bar(range(len(all_tasks)), debug=debug)
    for future in asyncio.as_completed(
        [problemData(task, session, csrf_token) for task in all_tasks]
    ):
        task, json = await future
        bar.update()
        bar.set_description(f"download tutorial for {task}")
        if json["success"] == "true":
            tutorials.append((task, json["html"]))
    await session.close()

    return tutorials


__all__ = ["get_token", "headers", "problemData", "xhr_tutorials"]
