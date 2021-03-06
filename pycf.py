import re
import sys
from os import getenv
from pathlib import Path

import arrow
import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from lxml.html import fromstring
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                             QSplitter, QTableWidget, QTableWidgetItem,
                             QTabWidget, QTextEdit, QTreeWidget, QVBoxLayout,
                             QWidget)

from cfdl.models import Contests, Tasks

load_dotenv()

session = requests.Session()

session.headers.update(
    {
        "User-Agent": "python-requests/2.25.1",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
)


dir_path = Path(".") / "cfdl"

env = Environment(
    loader=FileSystemLoader(f"{dir_path}/templates"),
    autoescape=select_autoescape(["html"]),
)


def render_tasks(tasks):
    return env.get_template("all.html").render(tasks=tasks)


def get_token(text):
    return re.findall(
        r'name=["\']csrf_token["\'] value=["\'](.*?)["\']',
        text,
    )[0]


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def login(self, session, handle, password):
        resp = session.post(
            "https://codeforces.com/enter",
            data={
                "csrf_token": get_token(
                    session.get("https://codeforces.com/enter").text
                ),
                "handleOrEmail": handle,
                "password": password,
                "remember": "on",
                "action": "enter",
            },
        )
        if resp.status_code != 200:
            print("Login Failed..")
            exit(0)
        if "Invalid handle/email or password" in resp.text:
            print("Login Failed. Invalid handle/email or password")
            exit(0)
        elif handle in resp.text:
            print("Login Success")
        else:
            print("Login Failed..")
            exit(0)

    def initUI(self):
        self.setWindowTitle("parser")
        self.HANDLE = getenv("HANDLE")
        self.PASSWORD = getenv("PASSWORD")

        self.login(session=session, handle=self.HANDLE, password=self.PASSWORD)

        splitter = QSplitter()
        left_layout = QVBoxLayout()

        self.browser = QWebEngineView()
        html = render_tasks([Tasks.get(Tasks.id == "1493A")])
        self.contest_id = "1493"
        self.browser.setHtml(html)

        left_layout.addWidget(self.browser)

        right_layout = QVBoxLayout()

        self.tab_widget = QTabWidget()

        self.text_edit = QTextEdit()
        right_layout.addWidget(self.tab_widget)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        self.init_contests()
        self.init_submissions()
        self.init_submit()
        self.load_submit()

        hbox = QHBoxLayout()

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        hbox.addWidget(splitter)

        self.setLayout(hbox)
        self.resize(1600, 1000)

    def init_contests(self):
        models = [t for t in Contests.select()]
        self.model_map = {}
        for c in models:
            self.model_map[str(c.contest_id)] = c

        self.contests = QTableWidget()
        self.contests.setColumnCount(2)
        self.contests.setHorizontalHeaderLabels(["№", "Название"])
        self.contests.verticalHeader().hide()
        self.contests.setColumnWidth(0, 100)
        self.contests.setColumnWidth(1, 500)
        self.contests.setEditTriggers(QTableWidget.NoEditTriggers)
        self.contests.cellClicked.connect(self.contest_clicked)

        lines = open("sep.txt").readlines()[::-1]
        self.contests.setRowCount(len(lines))

        self.tasks = QTableWidget()
        self.tasks.setColumnCount(3)
        self.tasks.setHorizontalHeaderLabels(["№", "Название", "Контест"])
        self.tasks.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tasks.cellClicked.connect(self.tasks_clicked)
        self.load_tasks(lines[0].split())

        for i, line in enumerate(lines):
            self.contests.setItem(i, 0, QTableWidgetItem(str(line)))
            names = ""
            for contests_id in line.split():
                names += self.model_map[contests_id].name + " "
            widget = QTextEdit(str(names))
            self.contests.setCellWidget(i, 1, widget)

        layout = QVBoxLayout()
        layout.addWidget(self.contests)
        layout.addWidget(self.tasks)

        widget = QWidget()
        widget.setLayout(layout)

        self.tab_widget.addTab(widget, "тренировка")

    def contest_clicked(self):
        row = self.contests.currentRow()
        self.load_tasks(self.contests.item(row, 0).text().split())

    def get_contest(self, problemcode):
        for i, char in enumerate(problemcode):
            if not char.isdigit():
                return problemcode[:i]

    def tasks_clicked(self):
        row = self.tasks.currentRow()
        task = Tasks.get(Tasks.id == self.tasks.item(row, 0).text().split())
        html = render_tasks([task])
        self.browser.setHtml(html)
        self.contest_id = self.get_contest(task.id)

        self.load_submit()

    def init_submissions(self):
        layout = QVBoxLayout()
        self.submissions = QTableWidget()
        self.submissions.setColumnCount(8)
        self.submissions.setHorizontalHeaderLabels(
            [
                "№",
                "Когда",
                "Кто",
                "Задача",
                "Язык",
                "Вердикт",
                "Время",
                "Память",
            ]
        )
        self.submissions.setEditTriggers(QTableWidget.NoEditTriggers)

        button = QPushButton("обновить")
        button.clicked.connect(self.load_submissions)

        layout.addWidget(self.submissions)
        layout.addWidget(button)

        widget = QWidget()
        widget.setLayout(layout)

        self.tab_widget.addTab(widget, "посылки")
        self.load_submissions()

    def init_submit(self):
        submit_layout = QGridLayout()
        self.task_combo = QComboBox()
        self.lang_combo = QComboBox()
        self.source = QTextEdit()
        submit_button = QPushButton("Отослать")
        submit_button.clicked.connect(self.submit)

        submit_layout.addWidget(QLabel("Задача"), 0, 0)
        submit_layout.addWidget(self.task_combo, 0, 1)

        submit_layout.addWidget(QLabel("Язык"), 1, 0)
        submit_layout.addWidget(self.lang_combo, 1, 1)

        submit_layout.addWidget(QLabel("Исходный код"), 2, 0)
        submit_layout.addWidget(self.source, 2, 1)
        submit_layout.addWidget(submit_button, 3, 0)

        submit_widget = QWidget()
        submit_widget.setLayout(submit_layout)

        self.tab_widget.addTab(submit_widget, "отослать")

    def load_submit(self):
        self.task_combo.clear()
        self.lang_combo.clear()
        html = session.get(
            f"https://codeforces.com/contest/{self.contest_id}/submit"
        ).text
        tree = fromstring(html)
        self.tasks_map = {}
        for element in tree.find_class("table-form")[0].xpath(
            "tr[1]/td[2]/label/select/option"
        )[1:]:
            self.tasks_map[element.text_content().strip()] = element.get(
                "value"
            )
            self.task_combo.addItems([element.text_content().strip()])

        options = tree.find_class("table-form")[0].xpath(
            "tr[3]/td[2]/select/option"
        )
        self.langs = {}
        for element in options:
            self.langs[element.text_content()] = element.get("value")
            self.lang_combo.addItems([element.text_content()])

    def load_submissions(self):
        self.submissions.setRowCount(20)
        submissions = requests.get(
            f"http://codeforces.com/api/user.status?handle={self.HANDLE}&from=1&count=20"
        ).json()

        if submissions["status"] != "OK":
            return

        submissions = submissions["result"]

        for i, submission in enumerate(submissions):
            for j, item in enumerate(
                [
                    submission["id"],
                    arrow.get(submission["creationTimeSeconds"]).humanize(
                        locale="ru"
                    ),
                    submission["author"]["members"][0]["handle"],
                    submission["problem"]["name"],
                    submission["programmingLanguage"],
                    submission.get("verdict", "testing")
                    + " "
                    + str(submission["passedTestCount"]),
                    submission["timeConsumedMillis"],
                    int(submission["memoryConsumedBytes"]) / 1000,
                ]
            ):
                self.submissions.setItem(i, j, QTableWidgetItem(str(item)))

    def load_tasks(self, contests):
        self.tasks.setRowCount(0)
        for contests_id in contests:
            tasks = Tasks.select().where(
                Tasks.contest_title == self.model_map[contests_id].name
            )
            for task in tasks:
                self.tasks.insertRow(self.tasks.rowCount())
                self.tasks.setItem(
                    self.tasks.rowCount() - 1,
                    0,
                    QTableWidgetItem(str(task.id)),
                )
                self.tasks.setItem(
                    self.tasks.rowCount() - 1,
                    1,
                    QTableWidgetItem(str(task.name)),
                )
                self.tasks.setItem(
                    self.tasks.rowCount() - 1,
                    2,
                    QTableWidgetItem(str(task.contest_title)),
                )

    def submit(self):
        submittedProblemIndex = self.tasks_map[
            str(self.task_combo.currentText())
        ]
        contestId = self.contest_id

        programTypeId = self.langs[str(self.lang_combo.currentText())]

        resp = session.get(
            f"https://codeforces.com/contest/{contestId}/submit"
        )

        token = get_token(resp.text)

        data = {
            "csrf_token": token,
            "action": "submitSolutionFormSubmitted",
            "submittedProblemIndex": submittedProblemIndex,
            "contestId": contestId,
            "programTypeId": programTypeId,
            "tabSize": 4,
            "source": self.source.toPlainText(),
            "sourceCodeConfirmed": "true",
        }
        r = session.post(
            "https://codeforces.com/contest/1480/submit?csrf_token=" + token,
            data=data,
        )

        self.load_submissions()


def main():
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
