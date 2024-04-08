import sqlite3


QUERY = "select domain, name, age, (select mark from photo as t where p.id = t.profile) from profile as p"


if __name__ == "__main__":
    connection = sqlite3.connect("database/database.sqlite")

    for (domain, name, age, mark) in connection.execute(QUERY).fetchall():
        print("{};{};{};{}".format(domain, name, age, mark))
