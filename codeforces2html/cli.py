# https://stackoverflow.com/questions/61933678/categorize-help-output-in-python-click
# https://stackoverflow.com/questions/62182687/custom-help-in-python-click/62437850
# https://github.com/willmcgugan/rich
# https://github.com/xalanq/cf-tool
# https://github.com/cp-tools/cf-tool
# cf download 1365-1367 1362A     (xhr support aiohttp !!!!!!!!!!!!)
# --pdf (generate pdf)    outfile update
# --refresh           not updated if task  in db
# --debug             +-
# --lang=ru         (translate)      -
# cf update         (git  update)    -
# cf pdf 1365-1367 1362A
#
# TODO xhr запрос на мини сервер когда закрытие
# "~/.cf/config" (как в flask-shop)
# 200 status code
#
#
#
# TODO
# 1. clean +
#    tutorial
# 2. --with-solution --with-code pdf command
# 3. code for task from top
# 4. link parser
# COMAND html + pdf
# --div(1/2/3) --range='A'-'B'

from rich.traceback import install

install()

import click

from . import codeforces2html
from . import pdf as topdf
from . import xhr
from .cli_help import DownloadHelp, OrderedGroup, PdfHelp
from .models import clean_database
from .utils import clean_contests, clean_tasks, problemset


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
@click.option("--pdf", is_flag=True)
@click.option("--debug", default=True, is_flag=True)
@click.option("--clean", default=False, is_flag=True)
@click.option("-t", "--tutorial", default=False, is_flag=True)
@click.argument("arguments", nargs=-1)
def download(arguments, clean, tutorial, pdf, debug):
    download_contests, download_tasks = parse_arguments(arguments)

    if clean:
        clean_database()

    codeforces2html.main(download_contests, download_tasks, debug=debug)

    if tutorial:
        xhr.main(download_contests, download_tasks, debug=debug)
    if pdf:
        topdf.generate(
            download_contests,
            download_tasks,
            ["1", "2", "3", "4"],
            [chr(i) for i in range(ord("A"), ord("Z") + 1)],
            False,
            False,
            True,
        )


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
    topdf.generate(
        download_contests,
        download_tasks,
        div,
        parse_task_option(letter),
        tutorial,
        code,
        True,
    )


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
def html(arguments, debug, div, letter, tutorial, code):
    download_contests, download_tasks = parse_arguments(arguments)
    topdf.generate(
        download_contests,
        download_tasks,
        div,
        parse_task_option(letter),
        tutorial,
        code,
        False,
    )


if __name__ == "__main__":
    cli()


__all__ = [
    "cli",
    "download",
    "html",
    "parse_arguments",
    "parse_task_option",
    "pdf",
]
