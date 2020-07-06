"""Console script for codeforces2html."""
import click


@click.group()
def cli():
    pass


from codeforces2html.utils import problemset
from codeforces2html import codeforces2html

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
            download_tasks.add(argument)
    codeforces2html.main(download_contests, download_tasks, tqdm_debug=True)


if __name__ == "__main__":
    cli()

# python3 cli.py download 1365-1367 1363-1366 1367A
