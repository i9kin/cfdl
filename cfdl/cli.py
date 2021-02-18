# https://stackoverflow.com/questions/61933678/categorize-help-output-in-python-click
# https://stackoverflow.com/questions/62182687/custom-help-in-python-click/62437850
# https://github.com/willmcgugan/rich
# https://github.com/xalanq/cf-tool
# https://github.com/cp-tools/cf-tool
import click
from rich.traceback import install

from . import aio, renders
from .cli_help import DownloadHelp, OrderedGroup, PdfHelp
from .models import Data, Tasks, clean_database
from .utils import clean_contests, clean_tasks

install()


@click.group(cls=OrderedGroup)
def cli():
    pass


def parse_arguments(arguments):
    download_contests = set()
    download_tasks = set()

    for argument in arguments:
        if "-" in argument:
            start, end = map(int, argument.split("-"))
            for contest_id in range(start, end + 1):
                download_contests.add(contest_id)
        elif not argument.isdigit():
            for i, char in enumerate(argument):
                if not char.isdigit():
                    if int(argument[:i]) not in download_contests:
                        download_tasks.add(argument)
                    break
        else:
            download_contests.add(int(argument))
    download_contests = clean_contests(download_contests)
    download_tasks = clean_tasks(list(download_tasks))
    return download_contests, download_tasks


@cli.command(cls=DownloadHelp)
@click.option("--debug", default=True, is_flag=True)
@click.option("--clean", default=False, is_flag=True)
@click.argument("arguments", nargs=-1)
def download(arguments, clean, debug):
    download_contests, download_tasks = parse_arguments(arguments)
    if clean:
        clean_database()

    data = Data()
    aio.download(data, download_contests, download_tasks, debug=debug)
    data.save()

    html = renders.render_tasks([t for t in Tasks().select()])
    open("tmp.html", "w").write(html)


def parse_task_option(options):
    letters = set()
    for option in options:
        option = option.upper()
        if "-" in option:
            index = option.find("-")
            first, second = option[:index], option[index + 1 :]
            for char in range(ord(first), ord(second) + 1):
                letters.add(chr(char))
        else:
            letters.add(option)
    return letters


@cli.command(cls=PdfHelp)
@click.argument("arguments", nargs=-1)
@click.option("--debug", default=True, is_flag=True)
@click.option(
    "--div",
    default=["1", "2", "3", "4"],
    type=click.Choice(["1", "2", "3", "4"]),
    multiple=True,
)
@click.option(
    "--letter",
    default=set(chr(i) for i in range(ord("A"), ord("Z") + 1)),
    type=str,
    multiple=True,
)
@click.option("-t", "--tutorial", default=False, is_flag=True)
@click.option("-c", "--code", default=False, is_flag=True)
def pdf(arguments, debug, div, letter, tutorial, code):
    download_contests, download_tasks = parse_arguments(arguments)
    pass


@cli.command(cls=PdfHelp)
@click.argument("arguments", nargs=-1)
@click.option("--debug", default=True, is_flag=True)
@click.option(
    "--div",
    default=["1", "2", "3", "4", "gl"],
    type=click.Choice(["1", "2", "3", "4", "gl"]),
    multiple=True,
)
@click.option(
    "--letter",
    default=set(chr(i) for i in range(ord("A"), ord("Z") + 1)),
    type=str,
    multiple=True,
)
@click.option("-t", "--tutorial", default=False, is_flag=True)
@click.option("-c", "--code", default=False, is_flag=True)
def html(arguments, debug, div, letter, tutorial, code):
    download_contests, download_tasks = parse_arguments(arguments)
    pass


def main():
    cli()


if __name__ == "__main__":
    main()


__all__ = [
    "cli",
    "download",
    "html",
    "main",
    "parse_arguments",
    "parse_task_option",
    "pdf",
]
