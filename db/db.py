from sqlalchemy import create_engine, text

class DB():

    def __init__(self, user, passwd, db):
        self.engine = create_engine("mariadb+mysqlconnector://" + user + ":" + passwd + "@localhost/" + db, echo=True)
        self.con = self.engine.connect()

    def save(self, data, table):
        keys = data.keys()
        print(data)
        query = text(f"insert into {table} ({','.join(keys)}) values ({','.join(map(lambda s: f':{s}', keys))})")
        self.con.execute(query, data)
