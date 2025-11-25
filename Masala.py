
import telebot      # Библиотека для работы с Telegram API
import time         # Модуль для работы со временем
from Database import*
from Search_engine import*
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand   # Для создания Inline-кнопок и команд меню (без BotFather)
from dotenv import load_dotenv
import logging      # Модуль для логирования ошибок
import os           # Модуль для работы с переменными окружения


# Загружаем переменные из .env
load_dotenv()

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = int(os.getenv("ADMIN_ID"))        # ID администратора бота, куда пользователям отправлять рецепты на проверку


# Создаём словарь для хранения данных каждого пользователя, т.к. Т-bot будет многопользовательский.

user_data = {}


# Функция для инициализации данных пользователя, если его ещё нет в user_data

def init_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "selected_ingredients": set(),
            "recipe_from_user": {
                "Название блюда": "",
                "Ингредиенты": [],
                "Способ приготовления": ""
            }
        }


# Функция для настройки меню бота
def setup_bot_commands():
    """Устанавливает команды меню для бота"""
    commands = [
        BotCommand("start", "Начало"),
        BotCommand("one", "Рецепты по ингредиентам"),
        BotCommand("two", "Поиск блюда по названию"),
        BotCommand("three", "Поиск блюда в меню бота"),
        BotCommand("description", "Описание бота"),
        BotCommand("feedback", "Обратная связь"),
        BotCommand("news", "Новости")
    ]

    bot.set_my_commands(commands)



# Создаем inline-кнопки для выбора пути:

def inline_menu():
    keyboard = InlineKeyboardMarkup(row_width = 1)  # row_width = 1 ставит кнопки в один столбик
    keyboard.add(
        InlineKeyboardButton("Рецепты по ингредиентам", callback_data = "first"),
        InlineKeyboardButton("Поиск блюда по названию", callback_data = "second"),
        InlineKeyboardButton("Поиск блюда в меню бота", callback_data = "third")
    )
    return keyboard

# Создаем inline-кнопки для выбора ингредиентов:

def inline_ingredients():
    keyboard = InlineKeyboardMarkup(row_width=1)  # row_width=1 сделает кнопки по 1 в ряд
    buttons = [InlineKeyboardButton(ingredient, callback_data = ingredient) for ingredient in ingredients]  # Список кнопок с ингредиентами
    keyboard.add(*buttons)  # Добавляем сразу все кнопки как отдельные аргументы
    keyboard.add(InlineKeyboardButton("✅ Готово", callback_data="done"))  # Добавляем кнопку для завершения выбора
    return keyboard

# Создаем inline-кнопки для выбора блюда из меню бота:

def inline_dishes():
    keyboard = InlineKeyboardMarkup(row_width=1)  # row_width=1 сделает кнопки по 1 в ряд
    buttons = [InlineKeyboardButton(dish, callback_data = dish) for dish in menu.keys()]  # Список кнопок с названиями блюд
    keyboard.add(*buttons)  # Добавляем сразу все кнопки как отдельные аргументы
    return keyboard

# Создаем inline-кнопки для выбора блюда из списка возможных блюд:

def inline_possible_dishes(possible_dishes):
    keyboard = InlineKeyboardMarkup(row_width=1)  # row_width=1 сделает кнопки по 1 в ряд
    buttons = [InlineKeyboardButton(dish, callback_data = dish) for dish in possible_dishes]  # Список кнопок с возможными блюдами
    keyboard.add(*buttons)  # Добавляем сразу все кнопки как отдельные аргументы
    return keyboard

# Создаем inline-кнопки для feedback:

def inline_feedback():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Хочу предложить свой рецепт блюда", callback_data="write"),
        InlineKeyboardButton("Хочу пожаловаться", callback_data="complaint"),
        InlineKeyboardButton("Ничего не хочу, меня всё устраивает", callback_data="cancel")
    )
    return keyboard

# Создаем inline-кнопки для отправки или отмены нового рецепта от пользователя:

def inline_send_recipe_to_admin():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Да, отправить", callback_data="send_recipe"),
        InlineKeyboardButton("Нет, не отправить", callback_data="cancel_recipe"),
    )
    return keyboard

# Создаем inline-кнопки для выбора сайта, где будет производиться поиск рецептов:

def inline_site():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("eda.ru", callback_data="site_edaru"),
        InlineKeyboardButton("1000.menu", callback_data="site_1000menu"),
        InlineKeyboardButton("iamcook.ru", callback_data="site_iamcook")
    )
    return keyboard



# Обработчик команд:

@bot.message_handler(commands=['description'])
def handle_description(message: telebot.types.Message):
    text = "Этот бот:\n" \
           "- подберёт рецепты блюд на основе ингредиентов, которые есть у тебя дома;\n" \
           "- поможет найти ссылку на рецепт приготовления желаемого блюда;\n" \
           "- предложит рецепты блюд из своего меню, которое периодически пополняется;\n" \
           "- ты можешь предложить свой рецепт, перейдя в Меню -> Обратная связь -> Хочу предложить свой рецепт\n\n" \
           "Для удобства взаимодействия с ботом в левом нижнем углу есть 'Меню'.\n\n" \
           "Вся работа с ботом построена на интерактивности: читай, выбирай, жмакай по кнопкам, пиши и отправляй свои сообщения.\n\n" \
           "Иногда будут появляться новости в соответствующем разделе 'Меню'. О новых рецептах и обновлениях ты сможешь узнать там.\n\n" \
           "Приветствуется содействие в расширении списка блюд:) Присылай свои рецепты. Если лень писать руками, то можешь скинуть ссылку. Админ проверит, попробует приготовить и внесёт в список."
    bot.reply_to(message, text)

@bot.message_handler(commands=['start'])
def tutorial(message: telebot.types.Message):
    init_user_data(message.chat.id)
    text = "Привет! Я - бот. Здесь я расскажу тебе, на что я способен, и как мы будем взаимодействовать друг с другом. " \
           "Любишь поесть, но не знаешь, что и как приготовить? Я постараюсь тебе помочь.\n\n" \
           "И так! У нас с тобой есть три пути:\n\n" \
           "    (1) - Рецепты по ингредиентам. Если в твоем холодильнике завалялись хоть какие-нибудь продукты, дай мне знать, а " \
           "я подберу тебе рецепт. Просто выбери из списка ингредиенты.\n\n" \
           "    (2) - Поиск блюда по названию. Напиши название блюда, а я скину тебе ссылку на рецепт его приготовления.\n\n" \
           "    (3) - Поиск блюда в меню бота. Выбери блюдо из моего меню и приготовь его.\n\n" \
           "Теперь определи свой путь. Напиши сообщение 1, 2 или 3, а лучше тапни по нужной кнопке."
    bot.send_message(message.chat.id, text, reply_markup=inline_menu())   # reply_markup=inline_menu() - добавление клавиатуры с inline-кнопками

@bot.message_handler(commands=['one'])
def handle_one(message: telebot.types.Message):
    user_id = message.chat.id
    init_user_data(message.chat.id)
    user_data[user_id]["selected_ingredients"].clear()  # При старте нового выбора ингредиентов очищаем предыдущий список
    text = "🔹 Выбери все продукты, которые есть у тебя дома:"
    bot.send_message(message.chat.id, text, reply_markup=inline_ingredients())  # reply_markup=inline_ingredients() - добавление клавиатуры с inline-кнопками

@bot.message_handler(commands=['two'])
def handle_two(message: telebot.types.Message):
    init_user_data(message.chat.id)
    text = "🔹 Выбери сайт для поиска рецептов: 🔹"
    bot.send_message(message.chat.id, text, reply_markup=inline_site())  # reply_markup=inline_site() - добавление клавиатуры с inline-кнопками

@bot.message_handler(commands=['three'])
def handle_three(message: telebot.types.Message):
    text = "🔹      Главное меню от шеф-повара:      🔹"
    bot.send_message(message.chat.id, text, reply_markup=inline_dishes())  # Добавление inline-кнопок с названиями блюд

@bot.message_handler(commands=['news'])
def handle_news(message: telebot.types.Message):
    news_text = "🔔 Новости и обновления:\n\n" + "\n\n".join(news_and_updates)
    bot.reply_to(message, news_text)

@bot.message_handler(commands=['feedback'])
def handle_feedback(message: telebot.types.Message):
    text = "✉ Здесь ты можешь оставить свой отзыв или предложение:"
    bot.send_message(message.chat.id, text, reply_markup=inline_feedback())  # Добавление inline-кнопок с feedback-ами



# Обработчик текстового ввода:

@bot.message_handler(content_types=['text'])
def number_way(message: telebot.types.Message):
    a = message.text.strip()
    if a == "1":
        handle_one(message)
    elif a == "2":
        handle_two(message)
    elif a == "3":
        handle_three(message)
    else:
        bot.reply_to(message, f"Что за '{a}'? \nСоберись мыслями и попробуй снова! \nВведи 1, 2 или 3. Либо вернись в 'Начало'.")



# Обработчики для Inline-кнопок:

@bot.callback_query_handler(func=lambda call: True)
def inline_button_handler(call):
    user_id = call.message.chat.id
    init_user_data(user_id)
    button = call.data       # Получаем callback_data

    sites = {
        "site_1000menu": "1000.menu",
        "site_iamcook": "iamcook.ru",
        "site_edaru": "eda.ru"
    }

    # Для кнопок выбора "пути":

    if button == "first":
        user_data[user_id]["selected_ingredients"].clear()  # Очищаем список при старте нового выбора ингредиентов
        text = "🔹 Выбери все продукты, которые есть у тебя дома: 🔹"
        bot.send_message(call.message.chat.id, text, reply_markup=inline_ingredients())  # Добавление inline-кнопок с ингредиентами
    elif button == "second":
        text = "🔹 Выбери сайт для поиска рецептов: 🔹"
        bot.send_message(call.message.chat.id, text, reply_markup=inline_site()) # Добавление inline-кнопок с сайтами
    elif button == "third":
        text = "🔹      Главное меню от шеф-повара:      🔹"
        bot.send_message(call.message.chat.id, text, reply_markup=inline_dishes())  # Добавление inline-кнопок с названиями блюд

    # Для кнопок выбора ингредиентов:

    elif button in ingredients:
        user_data[user_id]["selected_ingredients"].add(call.data)
        bot.answer_callback_query(call.id, text = f"Добавлено: {call.data}")

    elif button == "done":
        bot.answer_callback_query(call.id, text="Выбор завершен!")
        selected = user_data[user_id]["selected_ingredients"]        # Сохраняем список выбранных продуктов в переменную
        if not selected:    # Если список пустой
            bot.send_message(user_id, f"Ничего не выбрано!")
        else:
            selected_ingredients(user_id, selected)     # Передаем список `selected` в обработчик 'selected_ingredients'

    # Для кнопок выбора блюда:

    elif button in menu:
        ingredients_for_dish = "\n🔸".join(menu[button]["ингредиенты"])   # Получаем ингредиенты из словаря menu
        recipe = "\n🔸".join(menu[button]["рецепт"])                      # Получаем рецепт из словаря menu
        bot.send_message(call.message.chat.id, f"<b>\"{button}\"</b>\n\n"
                                               f"ИНГРЕДИЕНТЫ:\n🔸{ingredients_for_dish}\n\n"
                                               f"СПОСОБ ПРИГОТОВЛЕНИЯ:\n🔸{recipe}\n\n"
                                               f".................................................................", parse_mode = "HTML")
                                               # <b>...</b> и parse_mode = "HTML" - HTML-разметка для жирного шрифта

    # Для feedback-кнопок:

    elif button == "write":
        bot.send_message(user_id, "Введи название блюда:")
        bot.register_next_step_handler(call.message, get_recipe_name) # Передаем управление другому обработчику 'get_recipe_name'

    elif button == "complaint":
        bot.send_message(call.message.chat.id, "🤣 А больше ты ничего не хочешь?")

    elif button == "cancel":
        text = "Если тебя всё устраивает, тогда ты уже знаешь, что делать"
        bot.send_message(call.message.chat.id, text, reply_markup=inline_menu())

    # Для кнопок отправки сообщений админу:

    elif button == "send_recipe":
        recipe = user_data[user_id]["recipe_from_user"] # Сохраняем все полученные данные рецепта от пользователя в переменную
        recipe_text = f"*❗ Новый рецепт от пользователя ❗*\n\n" \
                      f"*Название блюда* - {recipe['Название блюда']}\n\n" \
                      f"*Ингредиенты:* \n{', '.join(recipe['Ингредиенты'])}\n\n" \
                      f"*Способ приготовления:* \n{recipe['Способ приготовления']}"
        bot.send_message(ADMIN_ID, recipe_text, parse_mode="Markdown")
        bot.send_message(user_id, "✅ Твой рецепт отправлен админу! Спасибо!")
        user_data[user_id]["recipe_from_user"].clear()  # Очищаем содержимое "recipe_from_user" после отправки сообщения от пользователя

    elif button == "cancel_recipe":
        bot.send_message(user_id, handle_feedback(call.message))

    # Для кнопок выбора сайта:

    elif button in sites:
        site = sites[button]  # Получаем сайт из словаря
        bot.send_message(call.message.chat.id, f"Отлично! Буду искать на {site}\n"
                                               f"Теперь напишите название блюда:")
        bot.register_next_step_handler(call.message, lambda msg: search_recipe_on_site(msg, site))



# Обработка сообщений после первичных обработчиков:

def selected_ingredients(user_id, selected):

    possible_dishes = []    # список возможных блюд из menu шеф-повара
    for name_dish, preparation in menu.items():
        if set(preparation["ингредиенты"]).issubset(set(selected)):
            possible_dishes.append(name_dish)

    ingredients_sets = [{'соль', 'хлеб', 'вода'}]  # список множества, содержащий все возможные варианты из кнопок 'соль', 'хлеб' и 'вода'

    selected_str = ", ".join(selected)
    bot.send_message(user_id, f"<b>Список выбранных продуктов:</b>\n{selected_str}", parse_mode = "HTML")
    if possible_dishes:
        text = "🔹           Ты можешь приготовить:           🔹"
        bot.send_message(user_id, text, reply_markup=inline_possible_dishes(possible_dishes))  # Добавление inline-кнопок с названиями возможных блюд
    elif selected_str == 'вода':
        bot.send_message(user_id, "Пей вода, ешь вода - ср..ть не будешь никогда!")
    elif selected_str == 'хлеб':
        bot.send_message(user_id, "Хлеб - всему голова!")
    elif selected_str == 'соль':
        bot.send_message(user_id, "Однократное употребление 250 грамм соли, приводит к летальному исходу!\n"
                                  "P.S. Пищевой соли, если что.")
    elif set(selected) == {'соль', 'хлеб'}:
        bot.send_message(user_id, "Хлеб с солью доедаешь? Тяжёлые у тебя времена. Могу только посочувствовать😢")
    elif set(selected) == {'вода', 'хлеб'}:
        bot.send_message(user_id, "Хлеб – твёрдый, вода – жидкая. Добавь усилий – получишь кашу. Приятного аппетита!")
    elif set(selected) == {'вода', 'соль'}:
        bot.send_message(user_id, "Соль в воде – это как шутка: если мало – не смешно, если много – неприятно.")
    elif set(selected) in ingredients_sets:
        bot.send_message(user_id, "А если ещё и свечи найдёшь, то можно устроить незабываемый ужин при свечах. Think about it!😄")
    else:
        bot.send_message(user_id, "Ничего не могу предложить. Просто съешь выбранные продукты!")

def search_recipe_on_site(message: telebot.types.Message, site: str):
    input_text = message.text.strip()
    # Обрабатываем команды
    commands = {
        "/description": handle_description,
        "/start": tutorial,
        "/one": handle_one,
        "/two": handle_two,
        "/three": handle_three,
        "/news": handle_news,
        "/feedback": handle_feedback
    }
    if input_text in commands:
        return commands[input_text](message)
    elif input_text in ["1", "2", "3"]:
        return number_way(message)
    else:
        # Ищем рецепты через Google Custom Search API
        bot.send_message(message.chat.id, "🔎  Ищу рецепты ...")
        recipes = search_recipes(input_text, site)
        if recipes == ["Рецепты не найдены!"]:
            bot.send_message(message.chat.id, "Рецепты не найдены!\n"
                                              "Проверь правильность написания или введи другое название блюда:")
            bot.register_next_step_handler(message, lambda msg: search_recipe_on_site(msg, site))  # Запрос нового ввода
        else:
            bot.send_message(message.chat.id, "\n".join(recipes))  # Отправляем найденные рецепты



# Заполнение формы нового рецепта от пользователя:

def get_recipe_name(message):
    user_id = message.chat.id
    user_data[user_id]["recipe_from_user"]["Название блюда"] = message.text         # Добавляем в словарь название блюда
    bot.send_message(user_id, "Напиши все ингредиенты (через запятую):")
    bot.register_next_step_handler(message, get_ingredients)         # Передаем управление обработчику 'get_ingredients'

def get_ingredients(message):
    user_id = message.chat.id
    ingred = message.text.split(",")                                 # Разделяем полученное сообщение на список подстрок
    user_data[user_id]["recipe_from_user"]["Ингредиенты"] = [ing.strip() for ing in ingred]
    bot.send_message(user_id, "Напиши способ приготовления (в свободной форме):")
    bot.register_next_step_handler(message, get_cooking_method)   # Передаем управление обработчику 'get_cooking_method'

def get_cooking_method(message):
    user_id = message.chat.id
    user_data[user_id]["recipe_from_user"]["Способ приготовления"] = message.text

    recipe = user_data[user_id]["recipe_from_user"]
    recipe_text = f"Проверь, всё ли верно\n\n" \
                  f"*Название блюда* - {recipe['Название блюда']}\n\n" \
                  f"*Ингредиенты:*\n{', '.join(recipe['Ингредиенты'])}\n\n" \
                  f"*Способ приготовления:*\n{recipe['Способ приготовления']}\n\n" \
                  f"Отправить этот рецепт админу?"

    bot.send_message(user_id, recipe_text, parse_mode="Markdown", reply_markup=inline_send_recipe_to_admin())
    # parse_mode = "Markdown" указывает, что текст содержит Markdown-разметку, позволяющую изменить текст:
    # Жирный - *текст* , Курсив - _текст_ , Моноширинный - `текст` , Ссылка - [текст](ссылка)



# Автоматический перезапуск бота и выявление ошибок, при возникновениии сбоя (в файле bot_errors.log и в терминале
# должна появиться подробная информация о причине ошибки):

logging.basicConfig(
    level=logging.ERROR,
    filename="bot_errors.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

setup_bot_commands()        # настройка меню бота при его запуске

while True:
    try:
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except telebot.apihelper.ApiException as e: # Ловит ошибки, связанные с API Telegram
        logging.error(f"ApiException: {e}")     # Записывает ошибку в bot_errors.log
        print(f"ApiException: {e}")             # Вывод ошибки в терминал
        time.sleep(5)                           # Если бот падает с ошибкой, то через 5 секунд он снова запустится
    except Exception as e:                      # Перехватывает любые другие ошибки
        logging.error(f"Другая ошибка: {e}")
        print(f"Другая ошибка: {e}")
        time.sleep(5)                           # Бот снова запускается через 5 секунд