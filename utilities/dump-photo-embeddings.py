import sqlite3
import pickle

QUERY = "SELECT p.path, p.mark, e.embedding FROM photo_embedding AS e INNER JOIN photo AS p ON (p.id = e.id)"

if __name__ == "__main__":
    connection = sqlite3.connect("database/database.sqlite")

    for (path, mark, data) in connection.execute(QUERY).fetchall():
        array = pickle.loads(data)
        like = 1 if mark == "like" else 0
        row = "{};{};{}".format(path, like, ";".join(map(str, array)))

        print(row)
