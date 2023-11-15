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
        self.conn = psycopg2.connect(database=database, password=password, user=user, host=host,
                                     port=port)
        self.cursor = self.conn.cursor()

    def getCursor(self):
        return self.cursor

    @dataBaseMethod
    def getValue(self, table, columns, condition=""):
        sql = f"SELECT {columns} FROM {table}" + " " + condition
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    @dataBaseMethod
    def updateValue(self, table, row, value, condition=""):
        sql = f"UPDATE {table} SET {row} = '{value}'" + " " + condition
        self.cursor.execute(sql)
        return 0

    @dataBaseMethod
    def deleteValue(self, table, condition=""):
        sql = f"DELETE FROM {table}" + " " + condition
        self.cursor.execute(sql)
        return 0

    @dataBaseMethod
    def insertCart(self, customer_id, product_id, taken_value):
        sql = f"INSERT INTO cart(customer_id, product_id, taken_value)  VALUES ({customer_id}, {product_id}, {taken_value})"
        self.cursor.execute(sql)
        return 0

    @dataBaseMethod
    def insertUser(self, user_id, phone, area, deleted):
        sql = f"INSERT INTO customer VALUES ({user_id}, '{phone}', '{area}', {deleted})"
        self.cursor.execute(sql)
        return 0

    @dataBaseMethod
    def free_request_no_fetch(self, req):
        self.cursor.execute(req)

    @dataBaseMethod
    def free_request_fetch(self, req):
        self.cursor.execute(req)
        return self.cursor.fetchall()

    def change_phone(self, new_phone, user_id):
        self.updateValue('customer', 'phone_number', new_phone, condition=f"WHERE tg_id = {user_id}")

    def delete_account(self, user_id):
        self.updateValue('customer', 'deleted', 1, condition=f"WHERE tg_id = {user_id}")

    def get_customer_data(self, user_id):
        return self.getValue("customer", "*", condition=f"WHERE tg_id = {user_id}")

    def get_product_data(self):
        return self.getValue("product", "*")

    def get_product_data_by_product_id(self, product_id):
        return self.getValue("product", "*", condition=f"WHERE product_id = {product_id}")

    def get_remainder_product(self, product_id):
        return self.getValue("product", "remainder", condition=f"WHERE product_id = {product_id}")

    def get_product_in_cart(self, user_id, product_id):
        return self.getValue("cart", "*", condition=f"WHERE customer_id = {user_id} AND product_id = {product_id}")

    def change_product_in_cart_taken_value(self, taken_value, new_value, user_id, product_id):
        self.updateValue("cart", "taken_value", taken_value + new_value,
                         condition=f"WHERE customer_id = {user_id} AND product_id = {product_id}")

    def get_cart_data(self, user_id):
        return self.free_request_fetch("SELECT product.name, product.cost, cart.taken_value "
                                       "FROM cart INNER JOIN product ON product.product_id = cart.product_id "
                                       f"WHERE customer_id = {user_id}")

    def get_product_data_by_user_id(self, user_id):
        return self.free_request_fetch("SELECT product.name, cart.product_id "
                                       "FROM cart INNER JOIN product ON cart.product_id = product.product_id "
                                       f"WHERE cart.customer_id = {user_id}")

    def delete_from_cart(self, product_id, user_id):
        self.free_request_no_fetch(f"DELETE FROM cart "
                                   f"WHERE cart.product_id = {product_id} AND cart.customer_id = {user_id}")

    def get_product_name_taken_value_remainder(self, user_id):
        return self.free_request_fetch(f"SELECT product.name, cart.taken_value, product.remainder "
                                       f"FROM cart INNER JOIN product ON cart.product_id = product.product_id "
                                       f"WHERE cart.customer_id = {user_id}")

    def insert_order(self, user_id, date, payment_method):
        return self.free_request_fetch(f"INSERT INTO orders(customer_id, date, payment_method, status) "
                                       f"VALUES({user_id}, '{date}', '{payment_method}', 0) RETURNING id;")

    def get_all_cart_data(self, user_id):
        return self.free_request_fetch(f"SELECT product_id, taken_value FROM cart WHERE customer_id = {user_id}")

    def insert_position(self, user_id, request):
        self.free_request_no_fetch(f"INSERT INTO positions(order_id, product_id, taken_value) VALUES {request}")

        self.free_request_no_fetch(f"DELETE FROM cart WHERE customer_id = {user_id}")

    def update_remainders_products(self, cart_data):
        for row in cart_data:
            self.free_request_no_fetch(
                f"UPDATE product SET remainder = remainder - {row[1]} WHERE product_id = {row[0]}")

    def get_order_data(self, user_id):
        return self.free_request_fetch(
            "SELECT orders.id, product.name, positions.taken_value, product.cost, "
            "orders.date, orders.payment_method, orders.status "
            "FROM orders INNER JOIN positions ON orders.id = positions.order_id "
            "INNER JOIN product ON positions.product_id = product.product_id "
            f"WHERE orders.customer_id = {user_id}")

    def get_product_ids(self):
        return [str(row[0]) for row in self.getValue("product", "product_id")]
