import io

import click
from rich.console import Console

from . import __version__

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
    + "  [cyan bold]--clean[/]        [white bold]Clean database before download.[/]\n"
    + "  [cyan bold]-t --tutorial[/]  [white bold]Download tutorial.[/]\n"
    + "  [cyan bold]--pdf[/]          [white bold]Generate pdf after download.[/]\n"
    + "  [cyan bold]--debug[/]        [white bold]Show progress bar.[/]\n",
)

arguments = io.StringIO()
arguments_console = Console(file=arguments, force_terminal=True)
arguments_console.print(
    "[magenta bold]Arguments:[/]\n"
    + "  [yellow bold]conetst[/]        {id}          Like 1364\n"
    + "  [yellow bold]conetst-range[/]  {start}-{end} Like 1364-1365\n"
    + "  [yellow bold]task[/]           {id}{letter}  Like [blue bold]1364A[/]\n",
)

pdf_options = io.StringIO()
pdf_console = Console(file=pdf_options, force_terminal=True)
pdf_console.print(
    "[red bold]Options for pdf and html command:[/]\n"
    + "  [cyan bold]--debug[/]        [white bold]Show progress bar.[/]\n"
    + "  [cyan bold]--div [[1|2|3|4][/][white bold](multiple) Division of the contest.[/]\n"
    + "  [cyan bold]--letter TEXT[/]  [white bold](multiple) Letter of the problem.[/] Like [blue bold]A[/] or [blue bold]A-C.[/]\n"
    + "  [cyan bold]-t --tutorial[/]  [white bold]Save the tasks if there is an tutorial.[/]\n"
    + "  [cyan bold]-c --code[/]      [white bold]Save the tasks if there has a code.[/]\n"
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
