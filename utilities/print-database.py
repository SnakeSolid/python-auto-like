import sqlite3
import sys

if __name__ == "__main__":
    connection = sqlite3.connect(sys.argv[1])

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

    for (mark, count) in connection.execute(
            "select mark, count(*) from photo group by mark order by mark"
    ).fetchall():
        print("N", mark, ":", count)

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

    print()
    print("-- photo embeddings --")

    for row in connection.execute("select * from photo_embedding").fetchall():
        print(row)
