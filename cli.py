"""Console script for codeforces2html."""
import click

from codeforces2html import codeforces2html, xhr
from codeforces2html.models import clean
from codeforces2html.utils import clean_contests, clean_tasks, problemset


@click.group()
def cli():
    pass


CONTEST_RANGE = 5

TASKS, last_contest = problemset()


@cli.command()
@click.argument("arguments", nargs=-1)
def download(arguments):

    download_contests = set()
    download_tasks = set()

    for argument in arguments:
        if "-" in argument:
            start, end = map(int, argument.split("-"))
            for contest_id in range(start, end + 1):
                download_contests.add(contest_id)
        else:
            for i, char in enumerate(argument):
                if not char.isdigit():
                    if int(argument[:i]) not in download_contests:
                        download_tasks.add(argument)
                    break

    download_contests = clean_contests(download_contests)
    download_tasks = clean_tasks(list(download_tasks))
    print(download_tasks, download_contests)
    codeforces2html.main(download_contests, download_tasks, debug=True)
    xhr.main(download_contests, download_tasks, debug=True)


# cf download 1365-1367 1362A     (xhr support aiohttp !!!!!!!!!!!!)
# --pdf (generate pdf)
# --refresh           not updated if task  in db
# --debug             +-
# --lang=ru         (translate)      -
# cf update         (git  update)    -
# cf pdf 1365-1367 1362A
#
# TODO xhr запрос на мини сервер когда закрытие
# "~/.cf/config" (как в flask-shop)
# 200 status code

if __name__ == "__main__":
    clean()
    cli()

# python3 cli.py download 1365-1367 1362A
