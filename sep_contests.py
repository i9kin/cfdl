from cfdl.models import Contests
from cfdl.utils import compare_contest


def main():
    contests = [t for t in Contests.select()]

    vals = {}
    for c in contests:
        vals[c.contest_id] = c

    used = [False for i in range(2000)]
    edges = [[] for i in range(2000)]

    for i in range(len(contests)):
        for j in range(len(contests)):
            if compare_contest(contest1=contests[i], contest2=contests[j]):
                edges[contests[i].contest_id].append(contests[j].contest_id)

    def dfs(v):
        used[v] = True
        a = []
        for u in edges[v]:
            if not used[u]:
                a += dfs(u)
        return [v] + a

    def compare_contests(contests):
        for i in range(len(contests)):
            for j in range(len(contests)):
                if not compare_contest(
                    contest1=contests[i], contest2=contests[j]
                ):
                    return False
        return True

    for v in range(2000):
        if v in vals and not used[v]:
            a = dfs(v)
            a = [vals[i] for i in a]
            # assert (compare_contests(a))
            if not compare_contests(a):
                print(a)
                for i in a:
                    print(i.contest_id)
                exit(0)
            for e in a:
                print(e.contest_id, end=" ")
            print()


main()
