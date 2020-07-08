import asyncio

import aiohttp
from lxml import html
from lxml.html import fromstring

from .bar_urils import Bar
from .models import Tasks
from .utils import TASKS, clean_contests, get_tasks, last_contest

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
}


async def get_token(session):
    resp = await session.get("https://codeforces.com/profile/MiFaFaOvO")
    async with resp:
        html = await resp.text()
        return (
            fromstring(html)
            .xpath('//*[@id="body"]/div[3]/div[5]/form/input[1]')[0]
            .get("value")
        )


async def problemData(task, session, csrf_token):
    resp = await session.post(
        "https://codeforces.com/data/problemTutorial",
        data={"problemCode": task, "csrf_token": csrf_token,},
        headers={
            "x-requested-with": "XMLHttpRequest",
            "x-csrf-token": csrf_token,
        },
    )
    async with resp:
        return (task, await resp.json())


async def parse(contests, additional_tasks, debug):
    session = aiohttp.ClientSession(headers=headers)
    loop = asyncio.get_event_loop()
    csrf_token = await get_token(session)

    all_tasks = additional_tasks.copy() + get_tasks(contests)
    all_tasks = [str(contest_id) + letter for contest_id, letter in all_tasks]

    task_map = {}
    bar = Bar(range(len(all_tasks)), debug=debug)
    for future in asyncio.as_completed(
        [problemData(task, session, csrf_token) for task in all_tasks]
    ):
        task, json = await future
        bar.update()
        bar.set_description(f"xhr task {task}")
        if json["success"] == "true":
            task_map[task] = json["html"]

    all_tasks = [task for task in task_map]

    task_models = Tasks.select().where(
        Tasks.id << [task for task in all_tasks]
    )
    for task in task_models:
        task.tutorial = task_map[task.id]
        task.save()
    await session.close()


def main(contests, additional_tasks, debug=True):
    asyncio.run(parse(contests, additional_tasks, debug=debug))


if __name__ == "__main__":
    main()
