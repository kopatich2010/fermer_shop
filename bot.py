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

    db.change_phone(phone, message.from_user.id)
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
    db.delete_account(message.chat.id)

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
    customer_data = db.get_customer_data(message.from_user.id)[0]
    bot.send_message(message.chat.id, f"Ваш номер {customer_data[1]}\nВаш район {customer_data[2]}",
                     reply_markup=markup_account_menu)


def products(message):
    try:
        bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id - 1, reply_markup=None)
    except Exception:
        pass
    bot.send_message(message.chat.id, "Поиск товаров", reply_markup=markup_account_products)

    data = db.get_product_data()
    suitable_data = list(filter(lambda row: float(row[3]) > 0.0, data))

    if not suitable_data or not data:
        bot.send_message(message.chat.id, "Товары закончились")
        return
    markup = tp.InlineKeyboardMarkup()
    for product in suitable_data:
        item = tp.InlineKeyboardButton(product[1], callback_data=product[0])
        markup.add(item)
    bot.send_message(message.chat.id, "Доступные на данный момент товары", reply_markup=markup)


def show_product_info(callback):
    product_id = callback.data[0]
    product_data = db.get_product_data_by_product_id(product_id)[0]
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

    remainder = float(db.get_remainder_product(product_id)[0][0])

    if not remainder:
        bot.send_message(callback.message.chat.id, "Товар закончился")
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
    cart_data = db.get_product_in_cart(callback.message.chat.id, product_id)

    if cart_data:
        cart_data = cart_data[0]
        db.change_product_in_cart_taken_value(taken_value, cart_data[3], callback.message.chat.id, product_id)
    else:
        db.insertCart(callback.message.chat.id, product_id, taken_value)
    bot.send_message(callback.message.chat.id, f"Продукт был успешно добавлен в вашу корзину",
                     reply_markup=markup_account_products)


def show_cart_products(message):
    data = db.get_cart_data(message.from_user.id)
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
        for row in data:
            sm = round(int(row[1]) * float(row[2]), 2)
            check.append(f"{row[0]} {row[1]}руб. * {row[2]}л\кг = {sm} рублей")
            cnt += sm
        check.append(f"Общая сумма товаров {cnt} р.")
        bot.send_message(message.chat.id, '\n'.join(check), reply_markup=markup)


def delete_cart_product(message):
    data = db.get_product_data_by_user_id(message.from_user.id)
    markup = tp.InlineKeyboardMarkup()
    for row in data:
        item = tp.InlineKeyboardButton(f"{row[0]}", callback_data=f"delete_product_from_cart  {row[1]}")
        markup.add(item)
    bot.send_message(message.from_user.id, "Что вы хотите удалить", reply_markup=markup)


def delete_cart_product_from_db(callback):
    product_id = callback.data.split()[1]
    db.delete_from_cart(product_id, callback.message.chat.id)
    bot.send_message(callback.message.chat.id, "Товар был убран из вашей корзины")


def make_order(callback):
    data = db.get_product_name_taken_value_remainder(callback.message.chat.id)
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

    order_id = db.insert_order(callback.message.chat.id, datetime_Vladivostok, callback.data.split()[1])

    cart_data = db.get_all_cart_data(callback.message.chat.id)

    request = ',\n'.join([f"({order_id[0][0]}, {row[0]}, {row[1]})" for row in cart_data])

    db.insert_position(callback.message.chat.id, request)
    db.update_remainders_products(cart_data)

    bot.send_message(callback.message.chat.id, "Заказа успешно оформлен ожидайте звонка", reply_markup=markup_menu)


def my_orders(message):
    data = db.get_order_data(message.from_user.id)
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
    customer_data = db.getValue("customer", "*", condition=f"WHERE tg_id = {message.chat.id if message.from_user.is_bot else message.from_user.id}")
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
    try:
        if message.text == 'Приступить':
            share_number(message)
        elif message.text == "Старт" or (not db.get_customer_data(message.from_user.id)):
            authorization(message)
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
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda callback: callback.data)
def choose(callback):
    print(callback.data)
    try:
        remove_markup(callback.message)
    except Exception:
        pass
    try:
        products_ids = db.get_product_ids()
        if callback.data.split()[0] in ['Центральный', 'Южный']:
            if len(callback.data.split()) == 2:
                phone = callback.data.split()[1]
                area = callback.data.split()[0]
                db.insertUser(callback.message.chat.id, phone, area, 0)
                greeting(callback.message)
            else:
                change_area(callback.message, callback.data)
        elif not db.get_customer_data(callback.message.chat.id):
            authorization(callback.message)
            return
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
        elif callback.data in products_ids:
            show_product_info(callback)
        else:
            bot.send_message(callback.message.chat.id, "Что то пошло не так")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    bot.polling(none_stop=True)
