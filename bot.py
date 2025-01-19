
import telebot
from telebot import types
import sqlite3
import random
import string
import time

TOKEN = "8183361179:AAE_wUvCa8P8M9GjHrtP59yF6riEJTlE-xU" # Замените на свой токен

SUPPORT_GROUP_ID = -1002295310441   # Замените на ID вашей группы поддержки

BOT_PROFILE_PHOTO_URL = "https://imgur.com/a/7TXTdQa"
ADMIN_TOOL_PHOTO_URL = "https://imgur.com/a/Nrcv8aB"

bot = telebot.TeleBot(TOKEN)

user_states = {}
active_questions = {}
support_stats = {}
ADMIN_IDS = [6714876522, 6920224572, 6529408254, 1033086078, 5418830185, 7412804687, 7534903812, 7085703705, 7035792901, 6632430184, 7828729512, 6869443741]
ADMIN_IDS = set(ADMIN_IDS)
DATABASE_FILE = 'support_bot.db'


def create_tables():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY
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
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("🍇Задать вопрос поддержке")
    markup.add(item1)
    bot.send_message(message.chat.id, "🍇Привет! Чем могу помочь?",
                   reply_markup=markup)
    add_user_to_db(message.from_user.id)
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.from_user.id, "🍇Приветствую саппорт! Для просмотра админ меню отправьте /admin")


@bot.message_handler(func=lambda message: message.text == "🍇Задать вопрос поддержке")
def ask_support(message):
    user_states[message.chat.id] = "waiting_for_question"
    bot.send_message(message.chat.id, "🍇Отправьте мне вопрос, который хотите задать поддержке:")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id in ADMIN_IDS:
        admin_tool(message)
    else:
        bot.send_message(message.chat.id, "🍇У вас нет доступа к этой команде")


@bot.message_handler(
    func=lambda message: message.chat.id in user_states and user_states[message.chat.id] == "waiting_for_question",
    content_types=['photo', 'text', 'video', 'document'])
def handle_support_message(message):
    user_id = message.chat.id
    username = message.from_user.username
    if username is None:
        username = "Не указан"

    send_to_support(message, user_id, username)
    bot.send_message(user_id, "🍇Ваш вопрос отправлен в поддержку.")
    del user_states[message.chat.id]


@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_question_'))
def answer_question_callback(call):
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

            active_questions[question_id]['answered'] = True
            add_answered_question_to_db(question_id)
            update_support_stats(message.from_user.id)
            bot.send_message(user_data['user_id'], f"🍇Саппорт ответил на ваш вопрос:\n{answer_text}")
            bot.send_message(message.chat.id, "🍇Ответ отправлен.")
        else:
            bot.send_message(message.chat.id, "🍇Вопрос уже был обработан.")

    except Exception as e:
        print(f"🍇Ошибка при обработке ответа: {e}")
        bot.send_message(message.chat.id, "🍇Произошла ошибка при отправке ответа.")
    del user_states[message.chat.id]
    
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text == "/")
def handle_slash_command(message):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("🍇A:Tool", callback_data='group_A_Tool')
    markup.add(item1)
    bot.send_message(message.chat.id, "🍇Выберите команду:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'group_A_Tool')
def group_A_Tool_callback(call):
    if call.from_user.id in ADMIN_IDS:
        admin_tool(call.message)
    else:
        bot.answer_callback_query(call.id, "🍇Вы не админ.")


def admin_tool(message):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("🍇Отправить сообщение всем", callback_data='send_all')
    item2 = types.InlineKeyboardButton("🍇Заблокировать человека", callback_data='block_user')
    item3 = types.InlineKeyboardButton("🍇Разблокировать человека", callback_data='unblock_user')
    markup.row(item1)
    markup.row(item2)
    markup.row(item3)
    bot.send_photo(message.chat.id, ADMIN_TOOL_PHOTO_URL, "🍇Выберите действие:",
                   reply_markup=markup)

@bot.callback_query_handler(
    func=lambda call: call.data in ['send_all', 'block_user', 'unblock_user'])
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


def get_all_bot_users():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


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

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"🍇Бот упал с ошибкой: {e}")
        time.sleep(1) 
