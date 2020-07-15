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
import io

from rich.traceback import install

install()

import click
from rich.console import Console

from codeforces2html import __version__, codeforces2html
from codeforces2html import pdf as topdf
from codeforces2html import xhr
from codeforces2html.models import clean_database
from codeforces2html.utils import clean_contests, clean_tasks, problemset


header = io.StringIO()
header_console = Console(file=header, force_terminal=True)
header_console.print(
    f":bar_chart:[white bold]codeforces {__version__}[/]\n"
    + f"Usage: cli.py download [red bold][[OPTIONS]][/] [magenta bold][[ARGUMENTS]]...[/]"
)

download_options = io.StringIO()
download_console = Console(file=download_options, force_terminal=True)
download_console.print(
    "[red bold]Options for download command:[/]\n"
    + "  [cyan bold]--clean[/]        [white bold]Clean database before download.[/white bold]\n"
    + "  [cyan bold]-t --tutorial[/]  [white bold]Download tutorial.[/white bold]\n"
    + "  [cyan bold]--pdf[/]          [white bold]Generate pdf after download.[/white bold]\n"
    + "  [cyan bold]--debug[/]        [white bold]Show progress bar.[/white bold]\n"
)

arguments = io.StringIO()
arguments_console = Console(file=arguments, force_terminal=True)
arguments_console.print(
    "[magenta bold]Arguments:[/]\n"
    + "  [yellow bold]conetst[/]        {id}          Like 1364\n"
    + "  [yellow bold]conetst-range[/]  {start}-{end} Like 1364-1365\n"
    + "  [yellow bold]task[/]           {id}{letter}  Like [blue bold]1364A[/]\n"
)

pdf_options = io.StringIO()
pdf_console = Console(file=pdf_options, force_terminal=True)
pdf_console.print(
    "[red bold]Options for pdf command:[/]\n"
    + "  [cyan bold]--debug[/]        [white bold]Show progress bar.[/white bold]\n"
)



class OrderedGroup(click.Group):
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs)

    def format_help(self, ctx, formatter):
        formatter.write(header.getvalue())
        self.format_commands(ctx, formatter)

    def format_commands(self, ctx, formatter):
        formatter.write(download_options.getvalue())
        formatter.write(pdf_options.getvalue())
        formatter.write(arguments.getvalue())

class CommandHelp(click.Command):
    def __init__(self, name=None, option=None, **attrs):
        self.option = option
        super().__init__(name, **attrs)

    def format_help(self, ctx, formatter):
        formatter.write(header.getvalue())
        self.format_options(ctx, formatter)
        formatter.write(arguments.getvalue())

    def format_options(self, ctx, formatter):
        formatter.write(self.option.getvalue())


class DownloadHelp(CommandHelp):
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs, option=download_options)

class PdfHelp(CommandHelp):
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs, option=pdf_options)

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
    RCPC = "00d28833206ccd9a67176c3190299d6e"
    download_contests, download_tasks = parse_arguments(arguments)
    
    if clean:
        clean_database()

    codeforces2html.main(download_contests, download_tasks, RCPC, debug=debug)

    if tutorial:
        xhr.main(download_contests, download_tasks, RCPC, debug=debug)
    if pdf:
        topdf.pdf(download_contests, download_tasks)


@cli.command(cls=PdfHelp)
@click.option("--debug", default=True, is_flag=True)
@click.argument("arguments", nargs=-1)
def pdf(arguments, debug):
    download_contests, download_tasks = parse_arguments(arguments)
    print(download_contests, download_tasks)
    #print(arguments, debug)
    #if pdf:
    topdf.html(download_contests, download_tasks, ['A', 'B', 'C'])


if __name__ == "__main__":
    cli()
