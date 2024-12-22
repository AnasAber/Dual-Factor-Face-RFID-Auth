import sqlite3

"""
(0, 'id', 'INTEGER', 0, None, 1)
(1, 'name', 'TEXT', 0, None, 0)
(2, 'card_uid', 'TEXT', 0, None, 0)
"""

con = sqlite3.connect("sql_db.db")

cur = con.cursor()

res = cur.execute("SELECT card_uid, name from users;")

res = res.fetchone()

# to fetch the result
print(res)

card_uid, name = res

print(f"name: {name}, id:{card_uid}")

con.commit()

con.close()


