# https://stackoverflow.com/questions/61933678/categorize-help-output-in-python-click
# https://stackoverflow.com/questions/62182687/custom-help-in-python-click/62437850
# https://github.com/willmcgugan/rich
# https://github.com/xalanq/cf-tool
# https://github.com/cp-tools/cf-tool
import click
from rich.traceback import install

from . import aio, renders
from .cli_help import DownloadHelp, OrderedGroup, PdfHelp
from .models import Contests, Data, Tasks, clean_database, save_contests

install()


@click.group(cls=OrderedGroup)
def cli():
    pass


from cfdl.models import clean_contests
from cfdl.utils import compare_contest


@cli.command(cls=DownloadHelp)
@click.option("--debug", default=True, is_flag=True)
@click.argument("arguments", nargs=-1)
def download(arguments, debug):
    # clean_contests()
    # save_contests(contests=aio.get_contests())
    # exit(0)

    a = arguments[0].split("-")
    start = int(a[0])
    end = int(a[1])

    all_contests = [t for t in Contests.select()]

    contest_range = list(range(start, end + 1))

    for contest_id in [874, 826, 589]:
        if contest_id in contest_range:
            contest_range.remove(contest_id)

    contests = [
        t
        for t in Contests.select().where(Contests.contest_id << contest_range)
    ]

    a = set()

    for contest1 in all_contests:
        for contest2 in contests:
            if compare_contest(contest1, contest2):
                a.add(contest1.contest_id)

    data = Data()

    aio.download(data, list(a), debug=debug)
    data.save()

    # html = renders.render_tasks([t for t in Tasks().select()])
    # open("tmp.html", "w").write(html)
    print("end")


def main():
    cli()


if __name__ == "__main__":
    main()

__all__ = ["cli", "dbg_compare", "download", "main"]
