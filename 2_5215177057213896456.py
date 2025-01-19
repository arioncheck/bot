
#  _____                              _
# / ____|                            | |
# | (___  _   _ _ __  _ __   ___  _ __| |_
# \___ \| | | | '_ \| '_ \ / _ \| '__| __|
# ____) | |_| | |_) | |_) | (_) | |  | |_
# |_____/ \__,_| .__/| .__/ \___/|_|_  \__|          _
# / ____|     | |   | |       / ____|              | |
# | |  __ _ __ |_|_ _|_|   ___| |     _ __ __ _  ___| | __
# | | |_ | '__/ _` | '_ \ / _ | |    | '__/ _` |/ __| |/ /
# | |__| | | | (_| | |_) |  __| |____| | | (_| | (__|   <
# \_____|_|  \__,_| .__/ \___|\_____|_|  \__,_|\___|_|\_\
#                 | |
#                 |_|

import telebot
from telebot import types
import sqlite3
import re
import random
import string

TOKEN = "8183361179:AAE_wUvCa8P8M9GjHrtP59yF6riEJTlE-xU"

ADMIN_IDS = [6714876522, 6578747825]
ADMIN_IDS = set(ADMIN_IDS)

SUPPORT_GROUP_ID = -1002358625921  

BOT_PROFILE_PHOTO_URL = "https://imgur.com/a/7TXTdQa"
ADMIN_TOOL_PHOTO_URL = "https://imgur.com/a/Nrcv8aB"

bot = telebot.TeleBot(TOKEN)

user_states = {}
blocked_users = set()
crack_messages = []
crack_message_counter = 0
support_users = set()
instruction_photo_url = "https://imgur.com/a/6It1Y6r"
instruction_text = "🍇Инструкция для саппорта:\n\n🍇Нажмите ответить под вопросом чтобы ответить человеку\n🍇Напишите A:Tool чтобы открыть админ меню\n🍇Это вся инструкция удачи сапорт."

active_questions = {}
support_stats = {}

DATABASE_FILE = 'bazadanix.db'


def create_tables():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_stats (
            user_id INTEGER PRIMARY KEY,
            answered_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answered_questions (
            question_id TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()


def load_blocked_users():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM blocked_users")
    blocked_user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(blocked_user_ids)


def load_support_stats():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, answered_count FROM support_stats")
    stats = {row[0]: {'answered_count': row[1]} for row in cursor.fetchall()}
    conn.close()
    return stats


def load_answered_questions():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT question_id FROM answered_questions")
    answered_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return answered_ids


def add_user_to_db(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def add_blocked_user_to_db(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO blocked_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def remove_blocked_user_from_db(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_bot_users():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def update_support_stats(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO support_stats (user_id) VALUES (?)", (user_id,))
        cursor.execute("UPDATE support_stats SET answered_count = answered_count + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"🍇Ошибка при обновлении статистики саппорта: {e}")
    finally:
        conn.close()

    if user_id in support_stats:
        support_stats[user_id]['answered_count'] += 1
    else:
        support_stats[user_id] = {'answered_count': 1}


def add_answered_question_to_db(question_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO answered_questions (question_id) VALUES (?)", (question_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def generate_random_question_id():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))


def send_to_support(message, user_id, username):
    question_id = generate_random_question_id()
    try:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            sent_message = bot.send_photo(SUPPORT_GROUP_ID, file_id,
                                          caption=f"🍇Вопрос #{question_id}\n🍇Текст: {message.caption if message.caption else '🍇Нет текста'}\n🍇Юзернейм: @{username}\n🍇ID: {user_id}",
                                          reply_markup=types.InlineKeyboardMarkup().add(
                                              types.InlineKeyboardButton("🍇Ответить",
                                                                         callback_data=f'answer_question_{question_id}')))
        elif message.content_type == 'video':
            file_id = message.video.file_id
            sent_message = bot.send_video(SUPPORT_GROUP_ID, file_id,
                                          caption=f"🍇Вопрос #{question_id}\n🍇Текст: {message.caption if message.caption else '🍇Нет текста'}\n🍇Юзернейм: @{username}\n🍇ID: {user_id}",
                                          reply_markup=types.InlineKeyboardMarkup().add(
                                              types.InlineKeyboardButton("🍇Ответить",
                                                                         callback_data=f'answer_question_{question_id}')))
        else:
            sent_message = bot.send_message(SUPPORT_GROUP_ID,
                                                f"🍇Вопрос #{question_id}\n🍇Текст: {message.text}\n🍇Юзернейм: @{username}\n🍇ID: {user_id}",
                                                reply_markup=types.InlineKeyboardMarkup().add(
                                                    types.InlineKeyboardButton("🍇Ответить",
                                                                               callback_data=f'answer_question_{question_id}')))

        active_questions[question_id] = {
            'user_id': user_id,
            'username': username,
            'message_id': sent_message.message_id,
            'question': message.text if message.text else message.caption,
            'answered': False,
            'group_message_id': sent_message.message_id
        }
    except Exception as e:
        bot.send_message(user_id, "🍇Произошла ошибка при отправке сообщения в поддержку. Попробуйте позже")
        print(f'🍇Ошибка в отправке сообщения: {e}')


@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == 'private')
def start(message):
    if message.from_user.id not in blocked_users:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = telebot.types.KeyboardButton("🍇Задать вопрос поддержке")
        item2 = telebot.types.KeyboardButton("🍇Показать кряк")
        markup.add(item1, item2)
        bot.send_photo(message.chat.id, photo="https://imgur.com/a/B7GBKXZ"
                                              "", caption="🍇Привет! Чем могу помочь?",
                       reply_markup=markup)
        add_user_to_db(message.from_user.id)
        if message.from_user.id in ADMIN_IDS:
            bot.send_message(message.from_user.id, "🍇Приветствую саппорт! Для просмотра инструкции отправьте /manual")
    else:
        bot.send_message(message.chat.id, "🍇Вы заблокированы и не можете использовать этого бота")


@bot.message_handler(commands=['manual'])
def manual(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_photo(message.chat.id, photo=instruction_photo_url, caption=instruction_text)


@bot.message_handler(func=lambda message: message.text == "🍇Задать вопрос поддержке")
def ask_support(message):
    if message.from_user.id not in blocked_users:
        user_states[message.chat.id] = "waiting_for_question"
        bot.send_message(message.chat.id, "🍇Отправьте мне вопрос, который хотите задать поддержке:")
    else:
        bot.send_message(message.chat.id, "🍇Вы заблокированы и не можете использовать этого бота")


@bot.message_handler(func=lambda message: message.text == "🍇Показать кряк")
def show_crack(message):
    if message.from_user.id not in blocked_users:
        if crack_messages:
            try:
                for msg_data in crack_messages:
                    if msg_data['type'] == 'photo':
                        bot.send_photo(message.chat.id, msg_data['file_id'], caption=msg_data['caption'],
                                       parse_mode="HTML")
                    elif msg_data['type'] == 'video':
                        bot.send_video(message.chat.id, msg_data['file_id'], caption=msg_data['caption'],
                                       parse_mode="HTML")
                    elif msg_data['type'] == 'text':
                        bot.send_message(message.chat.id, msg_data['text'], parse_mode="HTML")
                    elif msg_data['type'] == 'document':
                        bot.send_document(message.chat.id, msg_data['file_id'], caption=msg_data['caption'],
                                          parse_mode="HTML")
                    else:
                        bot.send_message(message.chat.id, "🍇Неподдерживаемый тип сообщения")
            except Exception as e:
                print(f"🍇 Ошибка при отправке кряка пользователю: {e}")
                bot.send_message(message.chat.id, "🍇 Произошла ошибка при отправке кряка, проверьте формат сообщений")
        else:
            bot.send_message(message.chat.id, "🍇 Сообщения для кряка еще не установлены")
    else:
        bot.send_message(message.chat.id, "🍇Вы заблокированы и не можете использовать этого бота")


@bot.message_handler(
    func=lambda message: message.chat.id in user_states and user_states[message.chat.id] == "waiting_for_question",
    content_types=['photo', 'text', 'video', 'document'])
def handle_support_message(message):
    if message.from_user.id not in blocked_users:
        user_id = message.chat.id
        username = message.from_user.username
        if username is None:
            username = "Не указан"

        send_to_support(message, user_id, username)
        bot.send_message(user_id, "🍇Ваш вопрос отправлен в поддержку.")
        del user_states[message.chat.id]
    else:
        bot.send_message(message.chat.id, "🍇Вы заблокированы и не можете использовать этого бота")


@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_question_'))
def answer_question_callback(call):
    if call.from_user.id not in ADMIN_IDS and call.from_user.id not in support_users:
        bot.answer_callback_query(call.id, "🍇Вы не саппорт.")
        return
    question_id = call.data.split('_')[-1]
    if question_id in active_questions:
        if active_questions[question_id]['answered']:
            bot.answer_callback_query(call.id, "🍇На этот вопрос уже ответили.")
            return
        user_states[call.from_user.id] = f"waiting_answer_{question_id}"
        bot.send_message(call.from_user.id, "🍇Введите ответ на вопрос:",
                         reply_markup=types.ForceReply(selective=True))
        bot.answer_callback_query(call.id, "🍇Ожидаю ответа...")
        bot.send_message(SUPPORT_GROUP_ID, f"🍇Саппорт @{call.from_user.username} отвечает на вопрос #{question_id}")
    else:
        bot.answer_callback_query(call.id, "🍇Вопрос уже обработан или не существует.")


@bot.message_handler(
    func=lambda message: message.text and message.chat.id in user_states and user_states[message.chat.id].startswith(
        'waiting_answer_'))
def handle_answer_input(message):
    try:
        question_id = user_states[message.chat.id].split('_')[-1]
        answer_text = message.text
        if question_id in active_questions:
            user_data = active_questions[question_id]

            bot.send_message(SUPPORT_GROUP_ID,
                             f"🍇Саппорт @{message.from_user.username} ответил на вопрос #{question_id}\n🍇Ответ: {answer_text}",
                             parse_mode="HTML")

            for admin_id in ADMIN_IDS:
                bot.send_message(admin_id,
                                 f"🍇Сообщение #{question_id} решено саппортом @{message.from_user.username}",
                                 parse_mode="HTML")

            active_questions[question_id]['answered'] = True
            add_answered_question_to_db(question_id)  # Добавляем в бд
            update_support_stats(message.from_user.id)
            bot.send_message(user_data['user_id'], f"🍇Саппорт ответил на ваш вопрос:\n{answer_text}")
            bot.send_message(message.chat.id, "🍇Ответ отправлен.")
        else:
            bot.send_message(message.chat.id, "🍇Вопрос уже был обработан.")

    except Exception as e:
        print(f"🍇Ошибка при обработке ответа: {e}")
        bot.send_message(message.chat.id, "🍇Произошла ошибка при отправке ответа.")
    del user_states[message.chat.id]


@bot.message_handler(commands=['start'], func=lambda message: message.chat.type in ['group', 'supergroup'])
def start_group(message):
    bot.send_message(message.chat.id, "🍇Бот работает в личном чате!")


@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text == "/")
def handle_slash_command(message):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("🍇/manual", callback_data='group_manual')
    item2 = types.InlineKeyboardButton("🍇A:Tool", callback_data='group_A_Tool')
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "🍇Выберите команду:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'group_manual')
def group_manual_callback(call):
    bot.send_photo(call.message.chat.id, photo=instruction_photo_url, caption=instruction_text)


@bot.callback_query_handler(func=lambda call: call.data == 'group_A_Tool')
def group_A_Tool_callback(call):
    if call.from_user.id in ADMIN_IDS:
        admin_tool(call.message)
    else:
        bot.answer_callback_query(call.id, "🍇Вы не админ.")


@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS and message.text == "A:Tool")
def admin_tool(message):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("🍇Отправить сообщение всем", callback_data='send_all')
    item2 = types.InlineKeyboardButton("🍇Заблокировать человека", callback_data='block_user')
    item3 = types.InlineKeyboardButton("🍇Разблокировать человека", callback_data='unblock_user')
    item4 = types.InlineKeyboardButton("🍇Поставить кряки", callback_data='set_crack')
    item5 = types.InlineKeyboardButton("🍇Управление кряками", callback_data='manage_crack')
    item8 = types.InlineKeyboardButton("🍇Все админы", callback_data='list_admins')
    item9 = types.InlineKeyboardButton("🍇Мой профиль", callback_data='my_profile')
    markup.row(item1)
    markup.row(item2)
    markup.row(item3)
    markup.row(item4)
    markup.row(item5)
    markup.row(item8)
    markup.row(item9)
    bot.send_photo(message.chat.id, ADMIN_TOOL_PHOTO_URL, "🍇Выберите действие:",
                   reply_markup=markup)


@bot.callback_query_handler(
    func=lambda call: call.data in ['send_all', 'block_user', 'unblock_user', 'set_crack', 'manage_crack',
                                    'add_support', 'remove_support', 'list_admins', 'my_profile'])
def callback_inline(call):
    if call.data == 'send_all':
        bot.answer_callback_query(call.id, "🍇Зайдите в личные сообщения с ботом")
        user_states[call.from_user.id] = "waiting_all_message"
        bot.send_message(call.from_user.id, "🍇Введите текст сообщения для всех пользователей:")
    elif call.data == 'block_user':
        user_states[call.message.chat.id] = "waiting_block_user"
        bot.send_message(call.message.chat.id, "🍇Введите ID или username пользователя для блокировки:")
    elif call.data == 'unblock_user':
        user_states[call.message.chat.id] = "waiting_unblock_user"
        bot.send_message(call.message.chat.id, "🍇Введите ID или username пользователя для разблокировки:")
    elif call.data == 'set_crack':
        bot.answer_callback_query(call.id, "🍇Зайдите в личные сообщения с ботом")
        user_states[call.from_user.id] = "waiting_crack_messages"
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("🍇Хватит", callback_data='finish_crack_messages')
        markup.add(item1)
        bot.send_message(call.from_user.id, "🍇Отправьте сообщение для кряка:", reply_markup=markup)
    elif call.data == 'manage_crack':
        user_states[call.message.chat.id] = "managing_crack_messages"
        show_crack_management_menu(call.message)
    elif call.data == 'list_admins':
        list_all_admins(call.message)
    elif call.data == 'my_profile':
        show_support_profile(call.from_user, call.message)


def show_support_profile(user, message):
    user_id = user.id
    try:
        user_data = bot.get_chat(user_id)
        username = user_data.username if user_data.username else "Не указан"
        profile_text = f"🍇Профиль саппорта\n🍇ID: {user_id}\n🍇Юзернейм: @{username}\n"
        if user_id in support_stats:
            profile_text += f"🍇Отвечено на вопросов: {support_stats[user_id]['answered_count']}"
        else:
            profile_text += f"🍇Отвечено на вопросов: 0"

        bot.send_photo(message.chat.id, BOT_PROFILE_PHOTO_URL, profile_text)
    except Exception as e:
        bot.send_message(message.chat.id, "🍇Произошла ошибка при получении вашего профиля")
        print(f"🍇Ошибка в профиле саппорта: {e}")


def list_all_admins(message):
    if ADMIN_IDS:
        admin_list_text = "🍇Список админов:\n"
        for admin_id in ADMIN_IDS:
            try:
                user = bot.get_chat(admin_id)
                username = user.username if user.username else "Не указан"
                admin_list_text += f"🍇ID: {admin_id}, Юзернейм: @{username}\n"
            except Exception:
                admin_list_text += f"🍇ID: {admin_id}, Юзернейм: Не удалось получить\n"
        bot.send_message(message.chat.id, admin_list_text)
    else:
        bot.send_message(message.chat.id, "🍇Нет админов")


def show_crack_management_menu(message):
    if not crack_messages:
        bot.send_message(message.chat.id, "🍇Сообщений для кряка нет.")
        del user_states[message.chat.id]
        return
    markup = types.InlineKeyboardMarkup()
    for i, msg_data in enumerate(crack_messages):
        msg_text = f"🍇Сообщение {i + 1}"
        if 'text' in msg_data and msg_data['text']:
            msg_text += f" (Текст: {msg_data['text'][:20]}...)"
        elif 'caption' in msg_data and msg_data['caption']:
            msg_text += f" (Описание: {msg_data['caption'][:20]}...)"
        markup.add(types.InlineKeyboardButton(msg_text, callback_data=f'manage_crack_msg_{i}'))
    markup.add(types.InlineKeyboardButton("🍇Закончить", callback_data='finish_manage_crack'))
    bot.send_message(message.chat.id, "🍇Выберите сообщение для управления:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('manage_crack_msg_'))
def manage_crack_message_selected(call):
    message_index = int(call.data.split('_')[-1])
    if 0 <= message_index < len(crack_messages):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🍇Удалить", callback_data=f'delete_crack_msg_{message_index}'))
        bot.send_message(call.message.chat.id, f"🍇Выберите действие для сообщения {message_index + 1}:",
                         reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "🍇Произошла ошибка, попробуйте еще раз.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_crack_msg_'))
def delete_crack_message(call):
    global crack_messages
    message_index = int(call.data.split('_')[-1])
    if 0 <= message_index < len(crack_messages):
        del crack_messages[message_index]
        bot.send_message(call.message.chat.id, f"🍇Сообщение {message_index + 1} удалено.")
        show_crack_management_menu(call.message)
    else:
        bot.send_message(call.message.chat.id, "🍇Произошла ошибка, попробуйте еще раз.")


@bot.callback_query_handler(func=lambda call: call.data == 'finish_manage_crack')
def finish_manage_crack(call):
    bot.send_message(call.message.chat.id, "🍇Управление кряками завершено.")
    del user_states[call.message.chat.id]


@bot.message_handler(
    func=lambda message: message.chat.id in user_states and user_states[
        message.chat.id] == "waiting_all_message", content_types=['photo', 'text', 'video', 'document'])
def handle_all_message(message):
    try:
        all_users = get_all_bot_users()
        for user_id in all_users:
            try:
                if message.content_type == 'photo':
                    file_id = message.photo[-1].file_id
                    bot.send_photo(user_id, file_id, caption=message.caption, parse_mode="HTML")
                elif message.content_type == 'video':
                    file_id = message.video.file_id
                    bot.send_video(user_id, file_id, caption=message.caption, parse_mode="HTML")
                elif message.content_type == 'text':
                    bot.send_message(user_id, message.text, parse_mode="HTML")
                elif message.content_type == 'document':
                    bot.send_document(user_id, message.document.file_id, caption=message.caption, parse_mode="HTML")
            except Exception as e:
                print(f'🍇Ошибка при отправке пользователю {user_id}: {e}')
        bot.send_message(message.chat.id, "🍇Сообщение отправлено всем пользователям.")
    except Exception as e:
        bot.send_message(message.chat.id, "🍇Произошла ошибка. Не удалось отправить сообщение всем пользователям.")
        print(f"🍇Ошибка при массовой рассылке: {e}")
    del user_states[message.chat.id]


@bot.message_handler(
    func=lambda message: message.chat.id in ADMIN_IDS and message.chat.id in user_states and user_states[
        message.chat.id] == "waiting_crack_messages", content_types=['photo', 'text', 'video', 'document'])
def handle_crack_messages(message):
    global crack_messages
    global crack_message_counter
    if message.from_user.id in ADMIN_IDS:
        msg_data = {}
        if message.content_type == 'photo':
            msg_data['type'] = 'photo'
            msg_data['file_id'] = message.photo[-1].file_id
            msg_data['caption'] = message.caption
        elif message.content_type == 'video':
            msg_data['type'] = 'video'
            msg_data['file_id'] = message.video.file_id
            msg_data['caption'] = message.caption
        elif message.content_type == 'text':
            msg_data['type'] = 'text'
            msg_data['text'] = message.text
        elif message.content_type == 'document':
            msg_data['type'] = 'document'
            msg_data['file_id'] = message.document.file_id
            msg_data['caption'] = message.caption

        crack_messages.append(msg_data)
        crack_message_counter += 1
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("🍇Хватит", callback_data='finish_crack_messages')
        markup.add(item1)
        bot.send_message(message.chat.id, "🍇Сообщение добавлено, добавить еще?", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "🍇Вы не администратор.")


@bot.callback_query_handler(func=lambda call: call.data == 'finish_crack_messages')
def finish_crack_messages(call):
    if call.from_user.id in ADMIN_IDS:
        bot.send_message(call.message.chat.id, "🍇Добавление кряков завершено.")
        del user_states[call.from_user.id]
    else:
        bot.send_message(call.message.chat.id, "🍇Вы не администратор.")


@bot.message_handler(
    func=lambda message: message.chat.id in user_states and user_states[
        message.chat.id] == "waiting_block_user")
def handle_block_user(message):
    try:
        user_id = None
        if message.text.isdigit():
            user_id = int(message.text)
        else:
            try:
                user = bot.get_chat(message.text)
                user_id = user.id
            except:
                bot.send_message(message.chat.id, "🍇Неверный ID или username пользователя.")
                del user_states[message.chat.id]
                return

        if user_id not in ADMIN_IDS:
            blocked_users.add(user_id)
            add_blocked_user_to_db(user_id)
            try:
                bot.send_message(user_id, "🍇Вы были заблокированы администратором.")
            except Exception:
                print(f"🍇Не удалось отправить сообщение о блокировке пользователю с ID: {user_id}")
            bot.send_message(message.chat.id, f"🍇Пользователь с ID {user_id} был заблокирован.")
        else:
            bot.send_message(message.chat.id, "🍇Нельзя заблокировать самого себя или администратора.")
    except Exception as e:
        bot.send_message(message.chat.id, "🍇Произошла ошибка при блокировке пользователя")
        print(f"🍇Ошибка при блокировке пользователя: {e}")
    del user_states[message.chat.id]


@bot.message_handler(
    func=lambda message: message.chat.id in ADMIN_IDS and message.chat.id in user_states and user_states[
        message.chat.id] == "waiting_unblock_user")
def handle_unblock_user(message):
    try:
        user_id = None
        if message.text.isdigit():
            user_id = int(message.text)
        else:
            try:
                user = bot.get_chat(message.text)
                user_id = user.id
            except:
                bot.send_message(message.chat.id, "🍇Неверный ID или username пользователя.")
                del user_states[message.chat.id]
                return
        if user_id not in ADMIN_IDS:
            if user_id in blocked_users:
                blocked_users.remove(user_id)
                remove_blocked_user_from_db(user_id)
                try:
                    bot.send_message(user_id, "🍇Вы были разблокированы администратором.")
                except Exception:
                    print(f"🍇Не удалось отправить сообщение о разблокировке пользователю с ID: {user_id}")
                bot.send_message(message.chat.id, f"🍇Пользователь с ID {user_id} был разблокирован.")
            else:
                bot.send_message(message.chat.id, f"🍇Пользователь с ID {user_id} не заблокирован.")
        else:
            bot.send_message(message.chat.id, "🍇Нельзя разблокировать администратора.")
    except Exception as e:
        bot.send_message(message.chat.id, "🍇Произошла ошибка при разблокировке пользователя")
        print(f"🍇Ошибка при разблокировке пользователя: {e}")
    del user_states[message.chat.id]


create_tables()
blocked_users = load_blocked_users()
support_stats = load_support_stats()
answered_questions = load_answered_questions()

for question_id in answered_questions:
    if question_id in active_questions:
        active_questions[question_id]['answered'] = True

print('Бот запущен')
bot.polling(none_stop=True)