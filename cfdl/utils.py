import html

from lxml.etree import tostring
from lxml.html import HtmlElement, fromstring

PROBLEMSET = {}
NAME = {}


def get_task(name, my_contest_id):
    """div1/2 contest"""
    contest_id = -1
    letter = -1
    for cur_contest_id, letter_ in NAME[name]:
        if abs(cur_contest_id - my_contest_id) < abs(
            contest_id - my_contest_id
        ):
            contest_id = cur_contest_id
            letter = letter_
    for t in PROBLEMSET[0][contest_id]:
        if t[0] == letter:
            return t.copy()


def tasks(name, range_contests):
    """div1/div2 fix return [div_1, div2] or [divX] like [(contest_id, letter), ...]"""
    contests = []
    for contest_id, letter in NAME[name]:
        if contest_id in range_contests:
            contests.append((contest_id, letter))
    return contests


def extend_problemset(contest_id, name, letter):
    global PROBLEMSET, NAME
    if contest_id not in PROBLEMSET:
        PROBLEMSET[contest_id] = [(name, letter)]
    else:
        PROBLEMSET[contest_id].append((name, letter))
    if name not in NAME:
        NAME[name] = [(contest_id, letter)]
    else:
        NAME[name].append((contest_id, letter))


def extend_task(id, tree):
    """Extend tasks like div1 div2 but api send div1"""
    tasks_xpath = '//*[@id="pageContent"]/div[2]/div[6]/table/tr'
    for i, task in enumerate(tree.xpath(tasks_xpath)[1:]):
        letter = task.xpath("td[1]/a")[0].text_content().strip()
        name = " ".join(
            task.xpath("td[2]/div/div[1]/a")[0].text_content().split()
        )
        extend_problemset(id, name, letter)


def get_condition(tree):
    task_element = tree.xpath('//*[@id="pageContent"]/div[2]')
    if len(task_element) == 0:
        return "pls open from codeforces.com"
    task_element = task_element[0]
    if len(task_element.find_class("diff-popup")) != 0:
        task_element = tree.xpath('//*[@id="pageContent"]/div[3]')[0]
    return get_html(task_element)


def get_contest_title(tree):
    contest_xpath1 = '//*[@id="sidebar"]/div[1]/table/tbody/tr[1]/th/a'
    contest_xpath2 = '//*[@id="sidebar"]/div[2]/table/tbody/tr[1]/th/a'  # 2
    element = tree.xpath(contest_xpath1)
    if element == []:
        element = tree.xpath(contest_xpath2)
    if len(element) == 0:
        return ""
    return element[0].text_content()


def validate_tutorials(materials):
    invalid_blogs = [
        "/blog/entry/3872",  # contest/133
        "/blog/entry/3254",  # contest/131
        "/blog/entry/419",  # contest/15
        "/blog/entry/431",  # contest/16
        "/blog/entry/192",  # contest/3
        # "/blog/entry/3770",
    ]
    urls = []
    for material in materials:
        if "Разбор задач" in material.text_content():
            link = material.get("href")
            if "blog" in link or "/blog/entry/" in link:
                valid = True
                for invalid_blog in invalid_blogs:
                    if invalid_blog in link:
                        valid = False
                        break
                if valid:
                    urls.append(link)
    return urls


def get_tutorials(tree: HtmlElement):
    """getting tutorial urls for the contest."""
    urls = []

    box = tree.find_class("roundbox sidebox sidebar-menu")

    if len(box) == 0:
        return []

    for url in validate_tutorials(box[0].xpath("ul/li/span[1]/a")):
        url = url.split("/")[-1]
        urls.append(f"https://codeforces.com/blog/entry/{url}?locale=ru")
    return urls


def get_codeforces_submition(html):
    xpath = '//*[@id="program-source-text"]'
    return fromstring(html).xpath(xpath)[0].text


def parse_link(url, html):
    if url.startswith("https://codeforces.com"):
        return get_codeforces_submition(html)
    elif url.startswith("https://pastebin.com/"):
        return html


def get_problemcode(url: str):
    url = (
        url.replace("http:", "")
        .replace("https:", "")
        .replace("codeforces", "")
        .replace(".com", "")
        .replace(".ru", "")
        .replace("..", "")
        .replace("www.", "")
    )

    if "problemset" in url:
        return url[
            url.find("problemset/problem/") + len("problemset/problem/") :
        ]
    return url[url.find("contest") + 8 :].replace("problem/", "")


def rewrite_link(link: str):
    if link.startswith("/"):
        link = "https://codeforces.com" + link
    return link


def parse_tutorial(html: HtmlElement, data, contests, blog_url):
    tree = fromstring(html)
    tree.rewrite_links(rewrite_link)
    childrens = tree.xpath('//*[@id="pageContent"]/div/div/div/div[3]/div')[
        0
    ].getchildren()
    htmls = []
    for element in childrens:
        urls = [e[2] for e in element.iterlinks()]
        problemTutorial = element.find_class("problemTutorial")
        add = True
        for url in urls:
            if "/problem/" not in url or "hackerearth" in url:
                continue

            problemcode = get_problemcode(url)
            contest_id = int(get_contest(problemcode))
            if contest_id not in contests:
                continue

            name = get_task_name(problemcode)
            eq_tasks = []
            for contest_id, letter in tasks(name, contests):
                eq_tasks.append(f"{contest_id}{letter}")
            if add:
                add = False
                for problemcode, html in htmls:
                    data.add_tutorial(problemcode, html, blog_url)
                htmls = []
            for problemcode in eq_tasks:
                htmls.append([problemcode, get_html(element)])
        if add:
            if len(problemTutorial) != 0:
                problemTutorial = problemTutorial[0]
                problemcode_ = problemTutorial.attrib["problemcode"]

                contest_id = int(get_contest(problemcode_))
                if contest_id not in contests:
                    continue

                if problemcode_ not in [
                    problemcode for problemcode, _ in htmls
                ]:
                    for problemcode, html in htmls:
                        data.add_tutorial(problemcode, html, blog_url)
                    name = get_task_name(problemcode_)
                    eq_tasks = []
                    for contest_id, letter in tasks(name, contests):
                        eq_tasks.append(f"{contest_id}{letter}")
                    htmls = []
                    for problemcode in eq_tasks:
                        htmls.append([problemcode, ""])
                for i, (problemcode, html) in enumerate(htmls):
                    problemTutorial.text = data.get_xhr_data(problemcode)
                    htmls[i][1] = htmls[i][1] + get_html(element)

            else:
                for i in range(len(htmls)):
                    htmls[i][1] = htmls[i][1] + get_html(element)
    for problemcode, html in htmls:
        data.add_tutorial(problemcode, html, blog_url)


def get_task_name(problemcode: str):
    contest = int(get_contest(problemcode))
    letter = get_letter(problemcode)
    for task_name, task_letter in PROBLEMSET[contest]:
        if task_letter == letter:
            return task_name


def get_html(tree):
    if type(tree) == str:
        return tree
    return html.unescape(
        tostring(tree, encoding="utf-8", pretty_print=True).decode("utf-8")
    )


def get_tasks(contests):
    all_tasks = []
    for contest in contests:
        for (
            _,
            letter,
        ) in PROBLEMSET[contest]:
            all_tasks.append((contest, letter))
    return all_tasks


def get_letter(problemcode):
    if "/" in problemcode:
        return problemcode.split("/")[1]
    else:
        for i, char in enumerate(problemcode):
            if not char.isdigit():
                return problemcode[i:]


def get_contest(problemcode):
    if "/" in problemcode:
        return problemcode.split("/")[0]
    else:
        for i, char in enumerate(problemcode):
            if not char.isdigit():
                return problemcode[:i]


def get_div(contest_name):
    m = [
        ["12", ["div. 1 + div. 2"]],
        ["2", ["div. 2", "div.2"]],
        ["1", ["div. 1", "div.1"]],
        ["3", ["div. 3", "div.3"]],
        ["4", ["div. 4", "div.4"]],
    ]
    for div, template in m:
        for string in template:
            if string in contest_name:
                return div, string
    return "?", ""


def get_sharp(contest_name):
    for word in contest_name.split():
        if word[0] == "#":
            return word[1:]
    return ""


def get_type(contest_id, contest_name):
    if "Experimental Educational Round: VolBIT Formulas Blitz" == contest_name:
        return {
            "val": "experimental educational round volbit formulas blitz",
            "sharp": "",
            "type": "",
        }

    if (
        contest_name
        == "Технокубок 2018 - Финал (только для онсайт-финалистов)"
    ):
        contest_name = "Technocup 2018 Final"

    if contest_name.startswith("School Personal Contest"):
        contest_name = " ".join(contest_name.split()[4:])

    contest_name = (
        contest_name.replace("(", "")
        .replace(")", "")
        .replace("base on", "based on")
    )
    contest_name = contest_name.lower()

    for string in [
        "rules",
        "codeforces round",
        "только для онсайт-финалистов",
        "onsite finalists only",
        "only for onsite-finalists",
        "spb finals",
        ",",
        ":",
        "(",
        ")",
        " - ",
        "[",
        "]",
        "unrated",
        "unrated mirror",
        "open online mirror",
        "unofficially",
        "open for everyone",
        "unofficial",
        "online-version",
        "online version",
        "acm-icpc",
        "rated for",
        "edition",
        "online",
        "mirror",
        "only",
        "rated",
    ]:
        contest_name = contest_name.replace(string, " ")
    contest_name = " ".join(contest_name.split()).replace(
        "private for onsite finalists", ""
    )

    m = [
        [
            "unrated cups",
            [
                "q#",
                "kotlin",
                "ceoi",
                "rockethon",
                "baltic olympiad",
                "all-ukrainian",
                "marathon",
                "language round",
                "school team",
                "april fools",
                "nerc",
                "programmers day",
            ],
        ],
        [
            "cups",
            [
                "технокубок",
                "technocup",
                "saratov, 2011",
                "looksery",
                "forethought",
                "grakn",
                "manthan",
                "canada cup",
                "zepto",
                "tinkoff",
                "memsql",
                "lyft",
                "avito",
                "8vc",
                "bubble cup",
                "croc",
                "coder-strike",
                "dasha",
                "abbyy",
                "huawei",
                "mail.ru",
                "yandex.algorithm",
                "vk cup",
            ],
        ],
    ]

    type = {}

    for key, template in m:
        for string in template:
            if string in contest_name:
                type["type"] = key + "/" + string

    tmp = contest_name.split()
    div_short, div = get_div(contest_name)
    type["div"] = div_short
    type["sharp"] = get_sharp(contest_name)

    if "based on" in contest_name.lower():
        type["based"] = " ".join(tmp[tmp.index("on") + 1 :])
        contest_name = contest_name.replace("based on", "").strip()

    if "educational" in contest_name:
        type["type"] = "educ/" + contest_name.split()[1]
    if "global round" in contest_name:
        type["type"] = "global/" + tmp[-1]
    if "good bye" in contest_name:
        type["type"] = "goodb/" + tmp[-1]
    if "hello" in contest_name:
        type["type"] = "hello/" + tmp[-1]
    if "kotlin" in contest_name:
        type["type"] = "kotlin/" + " ".join(tmp[2:])

    if "q#" in contest_name:
        type["type"] = (
            "q#/"
            + contest_name.replace("microsoft q# coding contest", "").strip()
        )

    if "beta round" in contest_name:
        type["type"] = "beta"
    if "alpha round" in contest_name:
        type["type"] = "alpha"
    if "testing round" in contest_name:
        type["type"] = "test"

    type["val"] = contest_name

    if "type" not in type:
        type["type"] = "round"
    return type


def get_tags(tree):
    tags = []
    for tag in tree.find_class("tag-box"):
        tags += tag.text_content().split()
    return tags


def task_jsonify(tree, contest_id, task_letter):
    obj = {
        "id": f"{contest_id}{task_letter}",
        "name": get_task_name(f"{contest_id}/{task_letter}"),
        "contest_title": get_contest_title(tree),
        "condition": get_condition(tree),
        "tutorial": "",
        "tags": ", ".join(get_tags(tree)),
    }
    return obj


def tasks_jsonify(data, tasks):
    json = []
    for contest_id, task_letter in tasks:
        json.append(
            task_jsonify(
                tree=data.get_task_tree(contest_id, task_letter),
                contest_id=contest_id,
                task_letter=task_letter,
            )
        )
    return json


from json import loads


def compare_contest(contest1, contest2):
    t1 = loads(contest1.type)
    t2 = loads(contest2.type)
    if t1 == t2:
        return True

    if (
        t1["sharp"] != ""
        and t1["sharp"] == t2["sharp"]
        and t1["type"] == t2["type"]
    ):
        return True

    if (
        t1["type"].startswith("educ")
        and t2["type"].startswith("educ")
        and t1["type"] == t2["type"]
    ):
        return True

    if (
        (t1["type"].startswith("cups") or t2["type"].startswith("cups"))
        and t1["type"] == t2["type"]
        and (
            ("based" not in t1 and "based" in t2 and t2["based"] == t1["val"])
            or (
                "based" not in t2
                and "based" in t1
                and t1["based"] == t2["val"]
            )
        )
    ):
        return True

    if (
        t1["type"].startswith("cups")
        and t1["type"] == t2["type"]
        and "based" in t1
        and "based" in t2
        and t1["based"] == t2["based"]
    ):
        return True

    return False


__all__ = [
    "NAME",
    "PROBLEMSET",
    "compare_contest",
    "extend_problemset",
    "extend_task",
    "get_codeforces_submition",
    "get_condition",
    "get_contest",
    "get_contest_title",
    "get_div",
    "get_html",
    "get_letter",
    "get_problemcode",
    "get_sharp",
    "get_tags",
    "get_task",
    "get_task_name",
    "get_tasks",
    "get_tutorials",
    "get_type",
    "parse_link",
    "parse_tutorial",
    "rewrite_link",
    "task_jsonify",
    "tasks",
    "tasks_jsonify",
    "validate_tutorials",
]
