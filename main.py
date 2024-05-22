# Импорт необходимых библиотек
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from argparse import ArgumentParser
import asyncio
import re
import json
import sqlite3
import unicodedata
import os
import tracemalloc

# Включение отслеживания памяти
tracemalloc.start()

# Создание директории для данных, если она не существует
if not os.path.exists("data"):
    os.makedirs("data")

# Создание аргументов для командной строки для передачи токена
parser = ArgumentParser(description='Telegram-бот с аргументом токена')
parser.add_argument('-t', '--token', type=str, help='Токен Telegram-бота')
args = parser.parse_args()
if not args.token: # если нет аргумента токена
    parser.error('Аргумент токена является обязательным. (-t TOKEN или --token TOKEN), --help для дополнительной информации.')

# Настройки API Telegram
api_id = 1
api_hash = 'b6b154c3707471f5339bd661645ed3d6'
bot_token = args.token
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Глобальные переменные для хранения данных пользователей и администраторов
usernames = {}
admins = {"ergolyam": True}
user_states_del_ = {}
user_states_add = {}

# Функция для создания подключения к базе данных
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

# Функция для вставки данных в базу данных
def insert_data(conn, data):
    cur = conn.cursor()
    cur.execute("SELECT MAX(id) FROM items")
    max_id = cur.fetchone()[0]
    if max_id is None:
        max_id = 0
    new_id = max_id + 1
    
    sql = ''' INSERT INTO items(id, item, item_info, quantity, price)
              VALUES(?, ?, ?, ?, ?) '''
    cur.execute(sql, (new_id, *data))
    conn.commit()
    return new_id

# Функция для удаления данных из базы данных и пересчета ID
def delete_and_sort(conn, id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"Элемент с id {id} не найден.")

    cur.execute("DELETE FROM items WHERE id = ?", (id,))

    cur.execute("UPDATE items SET id = id - 1 WHERE id > ?", (id,))
    conn.commit()

# Функция для получения данных из базы данных
def get_data(conn, id=None):
    if id is None:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items")
        rows = cur.fetchall()
        all_data = []
        for row in rows:
            all_data.append(row)
        return all_data
    else:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items WHERE id=?", (id,))
        row = cur.fetchone()
        if row:
            id, item, item_info, quantity, price = row
            return id, item, item_info, quantity, price
        else:
            return None

# Функции для обновления данных в базе данных
def update_quantity(conn, id, new_quantity):
    cur = conn.cursor()
    cur.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, id))
    conn.commit()
def update_price(conn, id, new_price):
    cur = conn.cursor()
    cur.execute("UPDATE items SET price = ? WHERE id = ?", (new_price, id))
    conn.commit()
def change_quantity(conn, id, change):
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM items WHERE id = ?", (id,))
    current_quantity = cur.fetchone()[0]
    new_quantity = current_quantity + change
    cur.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, id))
    conn.commit()

# Подключение к базе данных и создание таблицы, если её нет
items_data = create_connection("data/items_data.db")
with items_data:
    items_data.execute('''CREATE TABLE IF NOT EXISTS items
                (id INTEGER PRIMARY KEY,
                item TEXT NOT NULL,
                item_info TEXT,
                quantity INTEGER DEFAULT 0,
                price REAL DEFAULT 0.0)''')

# Асинхронная функция для начала работы с ботом и отображения главного меню
async def start(client, message, user, info_text):
    buttons = []
    if usernames.get(user.id) == None:
        usernames[user.id] = user.username
    if admins.get(usernames.get(user.id)):
        tag_adm = "Вы администратор."
        buttons.append([InlineKeyboardButton("Добавить товар", callback_data="add")])
        buttons.append([InlineKeyboardButton("Удалить товар", callback_data="del")])
    else:
        tag_adm = " "
    buttons.append([InlineKeyboardButton("Список товаров", callback_data="product")])
    keyboard = InlineKeyboardMarkup(buttons)
    await message.reply_text(f"{info_text}\nПривет {usernames.get(user.id)}!\n{tag_adm}", reply_markup=keyboard)
# Обработчик команды /start
@app.on_message(filters.command("start", prefixes="/"))
async def start_handle(client, message):
    await start(client, message, message.from_user, " ")

# Обработчик нажатий на кнопку "Добавить товар"
@app.on_callback_query(filters.regex("^add$"))
async def add_callback_handler(client, query):
    user = query.from_user
    if admins.get(usernames.get(user.id)):
        if user.id in user_states_add:
            del user_states_add[user.id]
        user_states_add[user.id] = "waiting_response"
        await query.message.edit_text("Введите имя товара:")
    else:
        await query.answer("Вы не админ!", show_alert=True)
    await query.answer()

# Обработчик нажатий на кнопку "Удалить товар"
@app.on_callback_query(filters.regex("^del$"))
async def del__callback_handler(client, query):
    user = query.from_user
    if admins.get(usernames.get(user.id)):
        if user.id in user_states_del_:
            del user_states_del_[user.id]
        user_states_del_[user.id] = "waiting_response"
        await query.message.edit_text("Введите имя id:")
    else:
        await query.answer("Вы не админ!", show_alert=True)
    await query.answer()

# Функция для отображения страницы с товарами
async def send_product_page(client, query, page_num):
    inline_keyboard = []
    text_message = "Список товаров:\n"
    start_index = (page_num - 1) * 5
    end_index = min(start_index + 5, len(get_data(items_data)))
    for id in range(start_index + 1, end_index + 1):
        item_id, item, item_info, quantity, price = get_data(items_data, id)
        inline_keyboard.append([InlineKeyboardButton(item, callback_data=str(id))])
    page_navigation = []
    if page_num > 1:
        page_navigation.append(InlineKeyboardButton("Предыдущая", callback_data=f"page_{page_num - 1}"))
    if end_index < len(get_data(items_data)):
        page_navigation.append(InlineKeyboardButton("Следующая", callback_data=f"page_{page_num + 1}"))
    if page_navigation:
        inline_keyboard.append(page_navigation)
    inline_keyboard.append([InlineKeyboardButton("Главное меню", callback_data="start_page")])
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await query.message.edit_text(text_message, reply_markup=reply_markup)

# Обработчик нажатий на кнопку "Список товаров"
@app.on_callback_query(filters.regex("^product$"))
async def product_callback_handler(client, query):
    await send_product_page(client, query, 1)

# Обработчик нажатий на кнопки навигации по страницам товаров
@app.on_callback_query(filters.regex(r'^page_\d+$'))
async def page_callback_handler(client, query):
    page_num = int(query.data.split('_')[1])
    await send_product_page(client, query, page_num)

# Глобальная переменная для хранения ID товаров
item_id_list = {}

# Обработчик нажатий на кнопки товаров
@app.on_callback_query(filters.regex(r'\b\d+\b'))
async def productget_callback_handler(client, query):
    item_id = int(query.data)
    item_id_list[query.message.id] = item_id
    id, item, item_info, quantity, price = get_data(items_data, item_id)
    text_message = f"Товар:\nID: {item_id}\nИмя: {item}\nОписание: {item_info}\nКол-Во: {quantity} шт\nЦена: {price} Руб"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Купить", callback_data="buy")],[InlineKeyboardButton("Главное меню", callback_data="start_page")]]) # Кнопка возврата в главное меню
    await query.message.delete()
    await query.message.reply_photo(
        photo=f"data/{item}.jpg",
        caption=text_message,
        reply_markup=reply_markup
        )

# Глобальная переменная для хранения ID покупателей
buyer_id_list = []

# Обработчик нажатий на кнопку "Купить"
@app.on_callback_query(filters.regex("^buy$"))
async def buy_callback_handler(client, query):
    item_id = item_id_list.get(query.message.id - 1)
    await query.message.delete()
    id, item, item_info, quantity, price = get_data(items_data, item_id)
    buyer_id_list.append(query.from_user.id)
    admins_username = []
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Подтвердить", callback_data="buy_accept")],
        [InlineKeyboardButton("Отклонить", callback_data="buy_override")]
        ]
    )
    for username in admins:
        if admins[username]:
            user = await client.get_users(username)
            admins_username.append(user.username)
            await client.send_message(user.id, f"Пользователь @{query.from_user.username} хочет купить у вас товар \"{item}\", его ID: {id}.", reply_markup=keyboard)
    admins_username_str = " @" + " @".join(admins_username)
    await start(client, query.message, query.from_user, f"Вы запросили покупку товара \"{item}\" за {price} Руб.\nНапишите этим пользователям для дальнейшей покупки: {admins_username_str}")

# Обработчик нажатий на кнопку "Подтвердить покупку"
@app.on_callback_query(filters.regex("^buy_accept$"))
async def buy_callback_handler(client, query):
    item_id = item_id_list.get(query.message.id - 2)
    buyer_id = buyer_id_list[-1]
    change_quantity(items_data, item_id, -1)
    id, item, item_info, quantity, price = get_data(items_data, item_id)
    await query.message.delete()
    await query.message.reply_text(f"Вы подтвердили покупку товара под ID: {item_id}\nОстаток: {quantity} шт")
    await client.send_message(buyer_id, f"Вашу покупку товара \"{item}\" подтвердили!")
    del item_id_list[query.message.id - 2]
    buyer_id_list.remove(buyer_id)

# Обработчик нажатий на кнопку "Отклонить покупку"
@app.on_callback_query(filters.regex("^buy_override$"))
async def buy_callback_handler(client, query):
    item_id = item_id_list.get(query.message.id - 2)
    buyer_id = buyer_id_list[-1]
    id, item, item_info, quantity, price = get_data(items_data, item_id)
    await query.message.delete()
    await query.message.reply_text(f"Вы отклонили покупку товара под ID: {item_id}")
    await client.send_message(buyer_id, f"Вашу покупку товара \"{item}\" отклонили!")
    del item_id_list[query.message.id - 2]
    buyer_id_list.remove(buyer_id)

# Обработчик нажатий на кнопку "Главное меню"
@app.on_callback_query(filters.regex("^start_page$"))
async def start_page_callback_handler(client, query):
    await query.message.delete()
    await start(client, query.message, query.from_user, " ")

# Глобальные переменные для хранения данных о товарах
item_list = []
item_info_list = []
item_quantity_list = []
item_price_list = []

# Обработчик текстовых сообщений и фотографий
@app.on_message(filters.photo | filters.text & ~filters.command(["start", "add", "tovars", "del"]))
async def say_handle_message(client, message):
    if message.from_user.id in user_states_add:
        if user_states_add[message.from_user.id] == "waiting_response":
            item = message.text
            item_list.append(item)
            del user_states_add[message.from_user.id]
            user_states_add[message.from_user.id] = "waiting_response_2"
            await message.reply_text("Введите описание товара:")
        elif user_states_add[message.from_user.id] == "waiting_response_2":
            item_info = message.text
            item_info_list.append(item_info)
            del user_states_add[message.from_user.id]
            user_states_add[message.from_user.id] = "waiting_response_3"
            await message.reply_text("Введите кол-во товара:")
        elif user_states_add[message.from_user.id] == "waiting_response_3":
            item_quantity = message.text
            item_quantity_list.append(item_quantity)
            del user_states_add[message.from_user.id]
            user_states_add[message.from_user.id] = "waiting_response_4"
            await message.reply_text("Введите цену товара:")
        elif user_states_add[message.from_user.id] == "waiting_response_4":
            item_price = message.text
            item_price_list.append(item_price)
            del user_states_add[message.from_user.id]
            user_states_add[message.from_user.id] = "waiting_response_5"
            await message.reply_text("Отправьте изображение товара:")
        elif user_states_add[message.from_user.id] == "waiting_response_5":
            await app.download_media(message.photo.file_id, f"data/{item_list[0]}.jpg")
            del user_states_add[message.from_user.id]
            insert_data(items_data, (str(item_list[0]), str(item_info_list[0]), int(item_quantity_list[0]), float(item_price_list[0])))
            info_text = f"Товар {str(item_list[0])} с описанием {str(item_info_list[0])} успешно добавлен!"
            await start(client, message, message.from_user, info_text)
            del item_list[:]
            del item_info_list[:]
            del item_quantity_list[:]
            del item_price_list[:]
    if message.from_user.id in user_states_del_:
        if user_states_del_[message.from_user.id] == "waiting_response":
            item_id = int(message.text)
            try:
                delete_and_sort(items_data, item_id)
                info_text = f"Товар под ID {item_id} успешно удалён!"
                all_data = get_data(items_data)
            except:
                info_text = f"Товар под ID {item_id} не существует!"
            finally:
                del user_states_del_[message.from_user.id]
                await start(client, message, message.from_user, info_text)

# Печать сообщения об успешном запуске бота и инициализация клиента
print("Бот успешно запущен!")
app.run() # Инициализация бота