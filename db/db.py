import sqlite3


class DB():

    def __init__(self, path):
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.cur = self.con.cursor()

    def save(self, data, table):
        cols = []
        vals = []
        marks = '(' + ','.join(['?'] * len(data)) + ')'

        for d in data:
            cols.append(d[0])
            vals.append(d[1])

        self.cur.execute(f"insert into {table} ({','.join(cols)}) values " + marks, vals)
        self.con.commit()
