import telebot
from telebot import types as tp
import database
import datetime
import pytz
from settings_to_connect import API_TOKEN

db = database.Database()

bot = telebot.TeleBot(API_TOKEN)

markup_account_menu = tp.ReplyKeyboardMarkup(resize_keyboard=True)
item1_m = tp.KeyboardButton('Назад')
item2_m = tp.KeyboardButton('Удалить аккаунт')
item3_m = tp.KeyboardButton('Изменить номер')
item4_m = tp.KeyboardButton('Изменить район')
item5_m = tp.KeyboardButton('Мои данные')
markup_account_menu.add(item1_m, item2_m, item3_m, item4_m, item5_m)

markup_account_products = tp.ReplyKeyboardMarkup(resize_keyboard=True)
item1_p = tp.KeyboardButton('Назад')
item2_p = tp.KeyboardButton('Доступные товары')
markup_account_products.add(item1_p, item2_p)

markup_menu = tp.ReplyKeyboardMarkup(resize_keyboard=True)
item1_mn = tp.KeyboardButton('Товары')
item2_mn = tp.KeyboardButton('Аккаунт')
item3_mn = tp.KeyboardButton('Корзина')
item4_mn = tp.KeyboardButton('Мои заказы')
markup_menu.add(item1_mn, item2_mn, item3_mn, item4_mn)

cart_markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
item1_c = tp.KeyboardButton('Назад')
item2_c = tp.KeyboardButton('Удалить продукт')
item3_c = tp.KeyboardButton('Моя корзина')
cart_markup.add(item1_c, item2_c, item3_c)


def greeting(message):
    try:
        bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id - 1, reply_markup=None)
    except Exception:
        pass
    bot.send_message(message.chat.id, "Добро пожаловать в наш магазин", reply_markup=markup_menu)


def remove_markup(message):
    bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id, reply_markup=None)


def share_number(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
    item = tp.KeyboardButton('Поделиться номером', request_contact=True)
    markup.add(item)
    bot.send_message(message.chat.id, "Для начала нам нужен ваш номер", reply_markup=markup)


def share_area(message):
    markup = tp.InlineKeyboardMarkup()
    item1 = tp.InlineKeyboardButton('Центральный',
                                    callback_data=f'Центральный {message.contact.phone_number}')
    item2 = tp.InlineKeyboardButton('Южный',
                                    callback_data=f'Южный {message.contact.phone_number}')
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Продолжим регистрацию", reply_markup=tp.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "Теперь выберите район в котором проживаете", reply_markup=markup)


def change_phone(message):
    phone = str(message.contact.phone_number) if str(message.contact.phone_number)[0] != '+' else str(
        message.contact.phone_number)[1:]

    db.updateValue('customer', 'phone_number', phone, condition=f"WHERE tg_id = {message.from_user.id}")
    bot.send_message(message.chat.id, "Вы успешно сменили номер телефона", reply_markup=markup_account_menu)


def change_area(message, area):
    db.updateValue('customer', 'area', area, condition=f"WHERE tg_id = {message.chat.id}")
    bot.send_message(message.chat.id, "Вы успешно сменили район", reply_markup=markup_account_menu)


def delete_customer_account(message):
    markup = tp.InlineKeyboardMarkup()
    item = tp.InlineKeyboardButton('Подтвердите удаление', callback_data='confirm_delete_customer')
    markup.add(item)
    bot.send_message(message.chat.id, "Если хотите полностью удалить аккаунт нажмите на кнопку", reply_markup=markup)


def delete_account(message):
    db.deleteValue("customer", condition=f"WHERE tg_id = {message.chat.id}")
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
    item = tp.KeyboardButton('Старт')
    markup.add(item)
    bot.send_message(message.chat.id, "Нажмите старт для продолжения", reply_markup=markup)


def change_customer_phone(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
    item = tp.KeyboardButton('Использовать мой номер телефона', request_contact=True)

    markup.add(item)
    bot.send_message(message.chat.id, "Отправьте мне карточку контакта", reply_markup=markup)


def change_customer_area(message):
    markup = tp.InlineKeyboardMarkup()
    item1 = tp.InlineKeyboardButton('Центральный', callback_data=f'Центральный')
    item2 = tp.InlineKeyboardButton('Южный', callback_data=f'Южный')
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Теперь выберите район в котором проживаете", reply_markup=markup)


def customer_account(message):
    customer_data = db.getValue("customer", "*", condition=f"WHERE tg_id = {message.from_user.id}")[0]
    bot.send_message(message.chat.id, f"Ваш номер {customer_data[1]}\nВаш район {customer_data[2]}",
                     reply_markup=markup_account_menu)


def products(message):
    try:
        bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id - 1, reply_markup=None)
    except Exception:
        pass
    bot.send_message(message.chat.id, "Поиск товаров", reply_markup=markup_account_products)

    data = db.getValue("product", "*")
    suitable_data = list(filter(lambda row: float(row[2]) > 0.0, data))
    if not suitable_data or not data:
        print("К сожалению товары закончились")
        return
    markup = tp.InlineKeyboardMarkup()
    for product in suitable_data:
        item = tp.InlineKeyboardButton(product[1], callback_data=product[0])
        markup.add(item)
    bot.send_message(message.chat.id, "Доступные на данный момент товары", reply_markup=markup)


def show_product_info(callback):
    product_data = db.getValue("product", "*", condition=f"WHERE product_id = {callback.data}")[0]
    markup = tp.InlineKeyboardMarkup()
    item1 = tp.InlineKeyboardButton("Добавить в корзину", callback_data=f"add_to_cart {product_data[0]}")
    markup.add(item1)
    msg = f"Название:  {product_data[1]}\n" \
          f"Цена за л./кг.:  {product_data[2]} рублей\n" \
          f"Оставшийся объём:  {product_data[3]} л./кг.\n" \
          f"{product_data[4]}"
    photo = product_data[5]
    bot.send_photo(callback.message.chat.id, photo, reply_markup=markup, caption=msg)


def pick_value(callback):
    product_id = callback.data.split()[1]

    remainder = float(db.getValue("product", "remainder", condition=f"WHERE product_id = {product_id}")[0][0])

    if not remainder:
        print("К сожалению этот товар закончился")
        return

    markup = tp.InlineKeyboardMarkup()
    items = []
    for value in range(5, 31, 5):
        value = round(value / 10, 1)
        if remainder >= value:
            item = tp.InlineKeyboardButton(f"{value}", callback_data=f"pick_value {value} {product_id}")
            items.append(item)
    markup.add(*items)
    bot.send_message(callback.message.chat.id,
                     f"Выберите объём (объём представлен в литрах или килограммах в зависимости от товара)",
                     reply_markup=markup)


def add_to_cart(callback):
    taken_value = float(callback.data.split()[1])
    product_id = int(callback.data.split()[2])
    cart_data = \
        db.getValue("cart", "*", condition=f"WHERE "
                                           f"customer_id = {callback.message.chat.id} AND product_id = {product_id}")
    if cart_data:
        cart_data = cart_data[0]
        db.updateValue("cart", "taken_value", taken_value + cart_data[3],
                       condition=f"WHERE customer_id = {callback.message.chat.id} AND product_id = {product_id}")
    else:
        db.insertCart(callback.message.chat.id, product_id, taken_value)
    bot.send_message(callback.message.chat.id, f"Продукт был успешно добавлен в вашу корзину",
                     reply_markup=markup_account_products)


def show_cart_products(message):
    data = db.free_request_fetch("SELECT product.name, product.cost, cart.taken_value "
                                 "FROM cart INNER JOIN product ON product.product_id = cart.product_id "
                                 f"WHERE customer_id = {message.from_user.id}")
    if not data:
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(tp.KeyboardButton("Назад"))
        bot.send_message(message.chat.id, "Ваша корзина пока что пуста")
    else:
        bot.send_message(message.chat.id, "Ваша корзина", reply_markup=cart_markup)

        markup = tp.InlineKeyboardMarkup()
        markup.add(tp.InlineKeyboardButton("Заказать", callback_data="make_order"))
        check = []
        cnt = 0
        # check = "\n".join([f"{row[0]} {row[1]}руб. * {row[2]}л\кг = {round(int(row[1]) * float(row[2]), 2)} рублей" for row in data])
        for row in data:
            sm = round(int(row[1]) * float(row[2]), 2)
            check.append(f"{row[0]} {row[1]}руб. * {row[2]}л\кг = {sm} рублей")
            cnt += sm
        check.append(f"Общая сумма товаров {cnt} р.")
        bot.send_message(message.chat.id, '\n'.join(check), reply_markup=markup)


def delete_cart_product(message):
    data = db.free_request_fetch("SELECT product.name, cart.product_id "
                                 "FROM cart INNER JOIN product ON cart.product_id = product.product_id "
                                 f"WHERE cart.customer_id = {message.from_user.id}")
    murkup = tp.InlineKeyboardMarkup()
    for row in data:
        item = tp.InlineKeyboardButton(f"{row[0]}", callback_data=f"delete_product_from_cart  {row[1]}")
        murkup.add(item)
    bot.send_message(message.from_user.id, "Что вы хотите удалить", reply_markup=murkup)


def delete_cart_product_from_db(callback):
    product_id = callback.data.split()[1]
    db.free_request_no_fetch(f"DELETE FROM cart "
                             f"WHERE cart.product_id = {product_id} AND cart.customer_id = {callback.message.chat.id}")
    bot.send_message(callback.message.chat.id, "Товар был убран из вашей корзины")


def make_order(callback):
    data = db.free_request_fetch(f"SELECT product.name, cart.taken_value, product.remainder "
                                 f"FROM cart INNER JOIN product ON cart.product_id = product.product_id "
                                 f"WHERE cart.customer_id = {callback.message.chat.id}")
    product_is_too_much = list(map(lambda row: (row[0], (float(row[1]) > float(row[2]))), data))
    for row in product_is_too_much:
        if row[1]:
            bot.send_message(callback.message.chat.id, f"Вы взяли слишком много {row[0].lower()}")
            return
    markup = tp.InlineKeyboardMarkup()
    markup.add(tp.InlineKeyboardButton("Безналичный", callback_data="load_order Безналичный"),
               tp.InlineKeyboardButton("Наличный", callback_data="load_order Наличный"))
    bot.send_message(callback.message.chat.id, "Выберите способ оплаты", reply_markup=markup)


def load_order(callback):
    tz_Vladivostok = pytz.timezone('Asia/Vladivostok')
    datetime_Vladivostok = datetime.datetime.now(tz_Vladivostok).strftime('%Y-%m-%d %H:%M:%S')
    bot.send_message(callback.message.chat.id, "Оформляем заказ")
    cur = db.getCursor()

    cur.execute(f"INSERT INTO orders(customer_id, date, payment_method, status) "
                f"VALUES({callback.message.chat.id}, '{datetime_Vladivostok}', '{callback.data.split()[1]}', 0)")

    cur.execute(f"SELECT id from orders WHERE customer_id = {callback.message.chat.id}")
    order_id = cur.fetchall()[-1][0]

    cur.execute(f"SELECT product_id, taken_value FROM cart WHERE customer_id = {callback.message.chat.id}")
    cart_data = cur.fetchall()

    request = ',\n'.join([f"({order_id}, {row[0]}, {row[1]})" for row in cart_data])

    cur.execute(f"INSERT INTO positions(order_id, product_id, taken_value) VALUES {request}")

    cur.execute(f"DELETE FROM cart WHERE customer_id = {callback.message.chat.id}")

    for row in cart_data:
        cur.execute(f"UPDATE product SET remainder = remainder - {row[1]} WHERE product_id = {row[0]}")

    bot.send_message(callback.message.chat.id, "Заказа успешно оформлен ожидайте звонка", reply_markup=markup_menu)


def my_orders(message):
    data = db.free_request_fetch(
        "SELECT orders.id, product.name, positions.taken_value, product.cost, "
        "orders.date, orders.payment_method, orders.status "
        "FROM orders INNER JOIN positions ON orders.id = positions.order_id "
        "INNER JOIN product ON positions.product_id = product.product_id "
        f"WHERE orders.customer_id = {message.from_user.id}")
    if not data:
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(tp.KeyboardButton("Назад"))
        bot.send_message(message.chat.id, "У вас пока что нет заказов")
    else:
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(tp.KeyboardButton("Назад"), tp.KeyboardButton("Мои заказы"))
        bot.send_message(message.chat.id, "Ваши заказы", reply_markup=markup)

        orders_ids = set(map(lambda x: x[0], data))
        for order_id in sorted(orders_ids):
            cnt = 0
            suitable_data = list(filter(lambda x: x[0] == order_id, data))
            date = suitable_data[0][4]
            payment_method = suitable_data[0][5]
            message_rows = [f'id заказа {order_id}']
            status = suitable_data[0][6]
            for row in suitable_data:
                message_rows.append(
                    f'{row[1]} {row[3]}р. {row[2]}кг./л. = {round(int(row[3]) * float(row[2]), 2)} рублей')
                cnt += round(int(row[3]) * float(row[2]), 2)
            message_rows.append(f'Всего {cnt} рублей')
            message_rows.append(f'{payment_method} расчет')
            message_rows.append(f'Дата заказа {date.strftime("%d-%m-%Y %H:%M:%S")}')
            if status == 1:
                message_rows.append(f'Статус доставлено')
            elif status == 0:
                message_rows.append('Статус ожидает доставки')

            msg = "\n".join(message_rows)
            bot.send_message(message.chat.id, msg)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    if not db.getValue("customer", "*", condition=f"WHERE tg_id = {message.from_user.id}"):
        share_area(message)
    else:
        change_phone(message)


@bot.message_handler(commands=['start'])
def authorization(message):
    customer_data = db.getValue("customer", "*", condition=f"WHERE tg_id = {message.from_user.id}")
    if customer_data:
        greeting(message)
    else:
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
        item = tp.KeyboardButton('Приступить')
        markup.add(item)
        bot.send_message(message.chat.id, "Вы не зарегистрированы в нашей системе.\n"
                                          "Желаете приступить к регистрации?", reply_markup=markup)


@bot.message_handler()
def select_option(message):
    try:
        bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id - 1, reply_markup=None)
    except Exception:
        pass
    if message.text == "Старт":
        authorization(message)
    elif message.text == 'Приступить':
        share_number(message)
    elif message.text in ['Товары', 'Доступные товары']:
        products(message)
    elif message.text == 'Аккаунт':
        customer_account(message)
    elif message.text in ['Корзина', 'Моя корзина']:
        show_cart_products(message)
    elif message.text == 'Назад':
        greeting(message)
    elif message.text == 'Удалить аккаунт':
        delete_customer_account(message)
    elif message.text == 'Удалить продукт':
        delete_cart_product(message)
    elif message.text == 'Изменить номер':
        change_customer_phone(message)
    elif message.text == 'Изменить район':
        change_customer_area(message)
    elif message.text == 'Мои данные':
        customer_account(message)
    elif message.text == 'Мои заказы':
        my_orders(message)


@bot.callback_query_handler(func=lambda callback: callback.data)
def choose(callback):
    remove_markup(callback.message)
    if callback.data.split()[0] in ['Центральный', 'Южный']:
        if len(callback.data.split()) == 2:
            phone = callback.data.split()[1]
            area = callback.data.split()[0]
            db.insertUser(callback.message.chat.id, phone, area)
            greeting(callback.message)
        else:
            change_area(callback.message, callback.data)
    elif callback.data == 'confirm_delete_customer':
        delete_account(callback.message)
    elif callback.data.split()[0] == "add_to_cart":
        pick_value(callback)
    elif callback.data.split()[0] == "pick_value":
        add_to_cart(callback)
    elif callback.data == "make_order":
        make_order(callback)
    elif callback.data.split()[0] == "load_order":
        load_order(callback)
    elif callback.data.split()[0] == "delete_product_from_cart":
        delete_cart_product_from_db(callback)
    else:
        if callback.data:
            show_product_info(callback)


if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception:
        pass
