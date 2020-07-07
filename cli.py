"""Console script for codeforces2html."""
import click

from codeforces2html import codeforces2html
from codeforces2html.models import clean
from codeforces2html.utils import clean_contests, clean_tasks, problemset

clean()


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


if __name__ == "__main__":
    cli()

# python3 cli.py download 1365-1367 1362A
