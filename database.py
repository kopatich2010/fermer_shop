import psycopg2
from settings_to_connect import database, password, user, host, port

class Database:

    def __init__(self):
        self.connect_to_db()

    @staticmethod
    def dataBaseMethod(func):
        def inner(self, *args, **kwargs):
            try:
                res = func(self, *args, **kwargs)
            except psycopg2.InterfaceError:
                try:
                    self.cursor.close()
                    self.cursor = self.conn.cursor()
                except Exception:
                    self.conn.close()
                    self.connect_to_db()
                res = func(self, *args, **kwargs)
            self.conn.commit()
            return res

        return inner

    def connect_to_db(self):
        self.conn = psycopg2.connect(database=database, password=password, user=user, host=host, port=port)
        self.cursor = self.conn.cursor()

    def getCursor(self):
        return self.cursor

    @dataBaseMethod
    def getValue(self, table, columns, condition=""):
        self.cursor.execute(f"SELECT {columns} FROM {table}" + " " + condition)
        return self.cursor.fetchall()

    @dataBaseMethod
    def updateValue(self, table, row, value, condition=""):
        self.cursor.execute(f"UPDATE {table} SET {row} = '{value}'" + " " + condition)
        return 0

    @dataBaseMethod
    def deleteValue(self, table, condition=""):
        self.cursor.execute(f"DELETE FROM {table}" + " " + condition)
        return 0

    @dataBaseMethod
    def insertCart(self, customer_id, product_id, taken_value):
        self.cursor.execute(
            f"INSERT INTO cart(customer_id, product_id, taken_value)  VALUES ({customer_id}, {product_id}, {taken_value})")
        return 0

    @dataBaseMethod
    def insertUser(self, user_id, phone, area):
        self.cursor.execute(f"INSERT INTO customer VALUES ({user_id}, '{phone}', '{area}')")
        return 0

    @dataBaseMethod
    def free_request_no_fetch(self, req):
        self.cursor.execute(req)

    @dataBaseMethod
    def free_request_fetch(self, req):
        self.cursor.execute(req)
        return self.cursor.fetchall()
