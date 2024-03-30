import sqlite3
import sys
import fire


def start(database_path: str,
          statistics: bool = True,
          embeddings: bool = False):
    connection = sqlite3.connect(database_path)

    print("-- statistics --")
    print("N profiles:",
          connection.execute("select count(*) from profile").fetchone()[0])
    print("N photos:",
          connection.execute("select count(*) from photo").fetchone()[0])
    print("N videos:",
          connection.execute("select count(*) from video").fetchone()[0])
    print(
        "N photo embeddings:",
        connection.execute("select count(*) from photo_embedding").fetchone()
        [0])
    print()

    n_like = 0
    n_dislike = 0

    for (mark, count) in connection.execute(
            "select mark, count(*) from photo group by mark order by mark"
    ).fetchall():
        if mark == "like":
            n_like = count
        elif mark == "dislike":
            n_dislike = count

        print("N", mark, ":", count)

    n_total = n_like + n_dislike

    if n_total > 0:
        print("  {:0.1f}% / {:0.1f}% (like / dislike)".format(
            100 * n_like / n_total, 100 * n_dislike / n_total))

    if not statistics:
        print()
        print("-- profiles --")

        for row in connection.execute("select * from profile").fetchall():
            print(row)

        print()
        print("-- photos --")

        for row in connection.execute("select * from photo").fetchall():
            print(row)

        print()
        print("-- videos --")

        for row in connection.execute("select * from video").fetchall():
            print(row)

    if embeddings:
        print()
        print("-- photo embeddings --")

        for row in connection.execute(
                "select * from photo_embedding").fetchall():
            print(row)


if __name__ == "__main__":
    fire.Fire(start)
