import pytest
from codeforces2html.utils import clean_tasks, clean_contests


def test_clean_tasks():
    assert clean_tasks(["1300a", "1301B", "1129A"]) == [
        [1300, "A"],
        [1301, "B"],
    ]
    assert clean_tasks(["50000A", "1300Q"]) == []
