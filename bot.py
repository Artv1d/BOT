import getInfAboutProduct
import telebot
import config
import sqlite3
import checkUser
import editUser
import checkCard

from telebot import types

import re
import os

user_states = {}

bot = telebot.TeleBot(config.TOKEN)
bot.set_webhook()

def mainKeyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bottom1 = types.KeyboardButton("Главная")
    bottom2 = types.KeyboardButton("Консультация")
    bottom3 = types.KeyboardButton("Заказ")
    markup.row(bottom1, bottom2)
    markup.add(bottom3)
    return markup

@bot.message_handler(commands=['start', 'main', 'hello'])
@bot.message_handler(func=lambda message: message.text.lower() == 'главная')
def welcome(message):
    #print(check_card_status(79965677951))
    # DB
    conn = sqlite3.connect('shop.sql')
    cur = conn.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(255), tgId varchar(20) '
        'unique not null, phone varchar(20), has_card integer default(0))')

    conn.commit()
    cur.close()
    conn.close()
    ###

    user_states[message.chat.id] = {'name': None, 'phone': None, 'tgId': None, 'card': 0}
    sti = open('static/welcome.webp', 'rb')

    bot.send_sticker(message.chat.id, sti)
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\n "
                                      "Я - <b>электронный сотрудник магазина по продаже тканей</b>, бот созданный чтобы помочь тебе сделать заказ.".format(
        message.from_user, bot.get_me()),
                     parse_mode='html')

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Статус посылки", callback_data='status')
    btn2 = types.InlineKeyboardButton("Сделать заказ", callback_data='order')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id,
                     "{0.first_name}, если вы хотите получить информацию по доставке вашего заказа - нажмите на <b>Статус посылки</b>\n"
                     "Если хотите сделать заказ - нажмите на <b>Сделать заказ</b>".format(message.from_user,
                                                                                          bot.get_me()),
                     parse_mode='html', reply_markup=markup)

@bot.message_handler(commands=['order'])
@bot.message_handler(func=lambda message: message.text.lower() == 'заказ')
def order(message):
    user_states[message.chat.id] = {'token': None}
    # bot.delete_message(message.chat.id, message.message_id - 2)
    #bot.send_message(message.chat.id, "Процесс создания заказа начат. Пожалуйста, следуйте инструкциям.",
                     #reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "Введите, пожалуйста, <b>артикул</b> товара\n"
                                      "<b>Пример ввода: 875234</b>\n\n"
                                      "Если вы забыли артикул товара, то можете перейти обратно в основной канал и посмотреть его\n"
                                      "<b>Вот ссылка -> https://t.me/bravissimo_nn</b>", parse_mode='html')
    bot.register_next_step_handler(message, get_token)
    # Обработка индефикатора и подтверждение правильности выбора товара


def get_token(message):
    # config.token = message.text.strip()
    # user_states[message.chat.id]['token':None]
    user_states[message.chat.id]['token'] = message.text.strip()
    # config.product_data = getInfAboutProduct.get_product_data(config.token)
    # user_states[message.chat.id]['product_data':None]
    user_states[message.chat.id]['product_data'] = getInfAboutProduct.get_product_data(
        user_states[message.chat.id]['token'])
    # Проверка на существование
    if (not user_states[message.chat.id]['product_data']):
        bot.send_message(message.chat.id, f'К сожалению такого артикула не существует😢\n'
                                          f'Попробуйте снова!')
        order(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        bottom1 = types.KeyboardButton("Верно")
        bottom2 = types.KeyboardButton("Неверно")
        bottom3 = types.KeyboardButton("Консультация")
        markup.row(bottom1, bottom2)
        markup.add(bottom3)

        bot.send_message(message.chat.id, "Проверьте, пожалуйста, что вы правильно ввели артикул\n"
                                          "Данные по данному артикулу:")

        # name = config.product_data[1]
        # price = config.product_data[3]
        # width = config.product_data[4]
        # token = config.product_data[5]
        # photo = config.product_data[2]  # Бинарные данные фотографии из базы данных
        # Сохранение бинарных данных фотографии в файл
        with open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'wb') as file:
            file.write(user_states[message.chat.id]['product_data'][2])
        # Отправка сообщения с данными о товаре и фотографией
        bot.send_photo(message.chat.id, open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'rb'),
                       caption=f'Name: {user_states[message.chat.id]['product_data'][1]}\n Price: {user_states[message.chat.id]['product_data'][3]}\n Width: {user_states[message.chat.id]['product_data'][4]}\n Token: {user_states[message.chat.id]['product_data'][5]}',
                       reply_markup=markup)
        os.remove(f'{user_states[message.chat.id]['product_data'][1]}.jpg')
        # Проверка на правильный выбор
        bot.register_next_step_handler(message, check_product)


def check_product(message):
    if (message.text.strip() == 'Неверно'):
        order(message)
    elif (message.text.strip() == 'Верно'):
        get_info_user(message)
    elif (message.text.strip() == 'Консультация'):
        consult2(message)
    else:
        bot.send_message(message.chat.id, "Выберите одну из кнопок: Верно или Невернно, либо выберите кнопку Консультация, для консультации с менеджером" )
        bot.register_next_step_handler(message, check_product)


def get_info_user(message):
    # Register users
    # user_states[message.chat.id]['user_data':None]
    user_states[message.chat.id]['user_data'] = checkUser.get_user_data(message.from_user.id)
    # config.user_data = checkUser.get_user_data(message.from_user.id)
    if (user_states[message.chat.id]['user_data']):
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
        bottom2 = types.InlineKeyboardButton('Изменились', callback_data='edit_data')
        markup.row(bottom1, bottom2)

        user_states[message.chat.id]['name'] = user_states[message.chat.id]['user_data'][1]
        user_states[message.chat.id]['phone'] = user_states[message.chat.id]['user_data'][3]
        user_states[message.chat.id]['tgId'] = message.from_user.id
        # config.name = config.user_data[1]
        # config.phone = config.user_data[3]
        # config.tg_id = config.user_data[2]

        bot.send_message(message.chat.id, f'Вы уже были в нашем магазине, и у нас есть ваши данные😁',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, f'Проверьте, пожалуйста, текущие данные на корректность:\n\n'
                                          f'ФИО: {user_states[message.chat.id]['user_data'][1]}\n'
                                          f'Номер телефона: {user_states[message.chat.id]['user_data'][3]}',
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Сейчас нужно вас зарегестрирвоать!\n"
                                          "Введите, пожалуйста, свои: Фамилия, Имя, Отчество",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, user_name)


def user_name(message):
    user_states[message.chat.id]['name'] = message.text.strip()
    if re.match(r'^[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+$', user_states[message.chat.id]['name']):
        # Ввод пользователя соответствует формату Фамилия Имя Отчество
        # config.name = full_name
        bot.send_message(message.chat.id, "Введите свой номер телефона в форматах:\n"
                                          "79*********")
        bot.register_next_step_handler(message, user_phone)
    else:
        # Ввод пользователя не соответствует формату ФИО
        bot.send_message(message.chat.id, "Пожалуйста, введите Фамилию Имя Отчество в правильном формате.")
        bot.register_next_step_handler(message, user_name)


def user_phone(message):
    user_states[message.chat.id]['phone'] = message.text.strip()
    if re.match(r'^79\d{9}$', user_states[message.chat.id]['phone']):
        # Введенный номер телефона соответствует формату
        # config.phone = message.text.strip()
        # config.tg_id = message.from_user.id

        user_states[message.chat.id]['tgId'] = message.from_user.id
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
        bottom2 = types.InlineKeyboardButton('Неверно', callback_data='false_enter')
        markup.row(bottom1, bottom2)

        bot.send_message(message.chat.id, f'Мы закончили небольшую регистрацию🔥')
        bot.send_message(message.chat.id,
                         f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]['name']}\n Номер телефона: {user_states[message.chat.id]['phone']}',
                         reply_markup=markup)
    else:
        # Неверный формат номера телефона
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер телефона.")
        bot.register_next_step_handler(message, user_phone)

def consult2(message):
    # name = config.product_data[1]
    # price = config.product_data[3]
    # width = config.product_data[4]
    # token = config.product_data[5]
    # photo = config.product_data[2]  #Бинарные данные фотографии из базы данных

    # Сохранение бинарных данных фотографии в файл
    with open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'wb') as file:
        file.write(user_states[message.chat.id]['product_data'][2])
    # Отправка сообщения с данными о товаре и фотографией
    bot.send_photo(config.manager_id, open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'rb'),
                   caption=f'Консультация!\n'
                           f'Информация о заказе с артикулом - {user_states[message.chat.id]['product_data'][5]}:\n'
                           f'Название: {user_states[message.chat.id]['product_data'][1]}\n'
                           f'Цена: {user_states[message.chat.id]['product_data'][3]}\n'
                           f'Ширина: {user_states[message.chat.id]['product_data'][4]}\n\n'

                           f'Информация о пользователе:\n'
                           f'Ник пользователя - {message.from_user.username}\n')
    os.remove(f'{user_states[message.chat.id]['product_data'][1]}.jpg')

    bot.send_message(message.chat.id,
                     f'Перейдите по следующей ссылке, чтобы связаться с менеджером. Обязательно представьтесь и отправьте артикул своего товара, чтобы менеджер смог вас понять)\n\n'
                     f'<b>Переходи сюда</b> -> https://t.me/res12245', parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['end_of_buy'])
@bot.message_handler(func=lambda message: message.text.lower() == 'завершение')

def take_size_from_user(message):
    bot.send_message(message.chat.id,
                     f'Введитесколько товара вы хотите заказать в САНТИМЕТРАХ', parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, end_of_work)
def end_of_work(message):
    config.size = message.text.strip()
    # name = config.product_data[1]
    # price = config.product_data[3]
    # width = config.product_data[4]
    # token = config.product_data[5]
    # photo = config.product_data[2]  #Бинарные данные фотографии из базы данных

    # Сохранение бинарных данных фотографии в файл
    with open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'wb') as file:
        file.write(user_states[message.chat.id]['product_data'][2])
    # Отправка сообщения с данными о товаре и фотографией
    bot.send_photo(config.manager_id, open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'rb'),
                   caption=f'Принять заказ!\n'
                           f'Информация о заказе с артикулом - {user_states[message.chat.id]['product_data'][5]}:\n'
                           f'Название: {user_states[message.chat.id]['product_data'][1]}\n'
                           f'Цена: {user_states[message.chat.id]['product_data'][3]}\n'
                           f'Ширина: {config.size}\n\n'

                           f'Информация о пользователе:\n'
                           f'Ник пользователя - {message.from_user.username}\n'
                           f'ФИО - {user_states[message.chat.id]['name']}\n'
                           f'Номер телефона - {user_states[message.chat.id]['phone']}\n'
                           f'Наличие карты - {"Есть карта" if user_states[message.chat.id]['card'] == 1 else "Нет карты"}')
    os.remove(f'{user_states[message.chat.id]['product_data'][1]}.jpg')

    bot.send_message(message.chat.id,
                     f'Ваш заказ зарегистрирован и отправлен менеджеру, в течение 12 рабочих часов менеджер свяжется с вами для приема оплаты', parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['advice'])
@bot.message_handler(func=lambda message: message.text.lower() == 'консультация')
def consult(message):
    # name = config.product_data[1]
    # price = config.product_data[3]
    # width = config.product_data[4]
    # token = config.product_data[5]
    # photo = config.product_data[2]  #Бинарные данные фотографии из базы данных

    # Сохранение бинарных данных фотографии в файл
    with open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'wb') as file:
        file.write(user_states[message.chat.id]['product_data'][2])
    # Отправка сообщения с данными о товаре и фотографией
    bot.send_photo(config.manager_id, open(f'{user_states[message.chat.id]['product_data'][1]}.jpg', 'rb'),
                   caption=f'Консультация!\n'
                           f'Информация о заказе с артикулом - {user_states[message.chat.id]['product_data'][5]}:\n'
                           f'Название: {user_states[message.chat.id]['product_data'][1]}\n'
                           f'Цена: {user_states[message.chat.id]['product_data'][3]}\n'
                           f'Ширина: {user_states[message.chat.id]['product_data'][4]}\n\n'

                           f'Информация о пользователе:\n'
                           f'Ник пользователя - {message.from_user.username}\n'
                           f'ФИО - {user_states[message.chat.id]['name']}\n'
                           f'Номер телефона - {user_states[message.chat.id]['phone']}\n'
                           f'Наличие карты - {"Есть карта" if user_states[message.chat.id]['card'] == 1 else "Нет карты"}')
    os.remove(f'{user_states[message.chat.id]['product_data'][1]}.jpg')

    bot.send_message(message.chat.id,
                     f'Перейдите по следующей ссылке, чтобы связаться с менеджером. Обязательно отправьте артикул своего товара, чтобы менеджер смог вас понять)\n\n'
                     f'<b>Переходи сюда</b> -> https://t.me/res12245', parse_mode='html',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['edit_name'])
@bot.message_handler(func=lambda message: message.text.lower() == 'фио')
def name(message):
    bot.send_message(message.chat.id, "Введите, пожалуйста, свои: Фамилия, Имя, Отчество",
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    # full_name = message.text.strip()
    user_states[message.chat.id]['name'] = message.text.strip()
    if re.match(r'^[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+$', user_states[message.chat.id]['name']):
        # config.name = full_name
        editUser.update_user_name(user_states[message.chat.id]['name'], message.from_user.id)
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
        bottom2 = types.InlineKeyboardButton('Неверно', callback_data='edit_data')
        markup.row(bottom1, bottom2)
        bot.send_message(message.chat.id,
                         f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]['name']}\n Номер телефона: {user_states[message.chat.id]['phone']}',
                         reply_markup=markup)
    else:
        # Ввод пользователя не соответствует формату ФИО
        bot.send_message(message.chat.id, "Пожалуйста, введите Фамилию Имя Отчество в правильном формате.")
        bot.register_next_step_handler(message, get_name)


@bot.message_handler(commands=['edit_phone'])
@bot.message_handler(func=lambda message: message.text.lower() == 'номер')
def phone(message):
    bot.send_message(message.chat.id, "Введите, пожалуйста, новый номер", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_phone)


def get_phone(message):
    # phone_nember = message.text.strip()
    user_states[message.chat.id]['phone'] = message.text.strip()
    if re.match(r'^79\d{9}$',
                user_states[message.chat.id]['phone']):
        # config.phone = phone_number
        editUser.update_user_phone(user_states[message.chat.id]['phone'], message.from_user.id)
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
        bottom2 = types.InlineKeyboardButton('Неверно', callback_data='edit_data')
        markup.row(bottom1, bottom2)
        bot.send_message(message.chat.id,
                         f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]['name']}\n Номер телефона: {user_states[message.chat.id]['phone']}',
                         reply_markup=markup)
    else:
        # Неверный формат номера телефона
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер телефона.")
        bot.register_next_step_handler(message, get_phone)


@bot.message_handler(commands=['edit_all'])
@bot.message_handler(func=lambda message: message.text.lower() == 'все')
def name_from_all(message):
    bot.send_message(message.chat.id, "Введите, пожалуйста, свои: Фамилия, Имя, Отчество",
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_name_from_all)


def get_name_from_all(message):
    # full_name = message.text.strip()
    user_states[message.chat.id]['name'] = message.text.strip()
    if re.match(r'^[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+$', user_states[message.chat.id]['name']):
        # config.name = full_name
        bot.send_message(message.chat.id, "Введите, пожалуйста, новый номер")
        bot.register_next_step_handler(message, get_all)
    else:
        # Ввод пользователя не соответствует формату ФИО
        bot.send_message(message.chat.id, "Пожалуйста, введите Фамилию Имя Отчество в правильном формате.")
        bot.register_next_step_handler(message, get_name_from_all)


def get_all(message):
    # phone_number = message.text.strip()
    user_states[message.chat.id]['phone'] = message.text.strip()
    if re.match(r'^79\d{9}$',
                user_states[message.chat.id]['phone']):
        # config.phone = phone_number
        editUser.update_user_all(user_states[message.chat.id]['phone'], user_states[message.chat.id]['name'],
                                 message.from_user.id)
        markup = types.InlineKeyboardMarkup()
        bottom1 = types.InlineKeyboardButton('Верно', callback_data='true_enter')
        bottom2 = types.InlineKeyboardButton('Неверно', callback_data='edit_data')
        markup.row(bottom1, bottom2)
        bot.send_message(message.chat.id,
                         f'Проверьте, пожалуйста, ваши данные на корректность:\n ФИО: {user_states[message.chat.id]['name']}\n Номер телефона: {user_states[message.chat.id]['phone']}',
                         reply_markup=markup)
    else:
        # Неверный формат номера телефона
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер телефона.")
        bot.register_next_step_handler(message, get_all)


@bot.message_handler(commands=['card'])
@bot.message_handler(func=lambda message: message.text.lower() == 'продолжаем')
def order_formation(message):
    bot.send_message(message.chat.id, f'Формирование заказа ???', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(content_types=['photo', 'video', 'audio', 'sticker', 'emoji'])
def noneContent(message):
    bot.reply_to(message, f'Извините, {message.from_user.first_name}, я не умею обрабатывать такие сообщения((')


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'status':
        bot.send_message(callback.message.chat.id,
                         'Перенаправляю Вас на моего коллегу, регистрация в один клик, далее введите <b>/add (номер вашего заказа)</b>, а затем <b>/tracks</b>. Также напоминаю, что по правилам нашего магазина (далее правила по срокам доставки)\n\n' + "Ссылка -> https://t.me/RLabbot",
                         parse_mode='html')
    # bot.delete_message(callback.message.chat.id, callback.message.message_id)
    elif callback.data == 'order':
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Заказ")
        markup1.add(item1)
        bot.send_message(callback.message.chat.id,
                         "Чтобы сделать заказ, отправьте команду <b>/order</b> или нажмите на кнопку <b>Заказ</b>",
                         parse_mode='html', reply_markup=markup1)
    elif callback.data == 'true_enter':
        user_states[callback.message.chat.id]['card'] = checkCard.check_card_status('cards.xlsx', user_states[callback.message.chat.id]['phone'])
        if not user_states[callback.message.chat.id]['user_data']:
            # Доделать
            conn = sqlite3.connect('shop.sql')
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO users(name, tgId, phone, has_card) VALUES ('{user_states[callback.message.chat.id]['name']}', '{user_states[callback.message.chat.id]['tgId']}', '{user_states[callback.message.chat.id]['phone']}', '{user_states[callback.message.chat.id]['card']}')")
            conn.commit()
            cur.close()
            conn.close()

        else:
            if (not user_states[callback.message.chat.id]['user_data'][4]) and user_states[callback.message.chat.id][
                'card']:
                editUser.update_user_card(user_states[callback.message.chat.id]['card'],
                                          user_states[callback.message.chat.id]['tgId'])

        if not user_states[callback.message.chat.id]['card']:
            markup = types.InlineKeyboardMarkup()
            bottom1 = types.InlineKeyboardButton('Хочу', callback_data='create_card')
            bottom2 = types.InlineKeyboardButton('Не хочу', callback_data='continue_without_card')
            markup.row(bottom1, bottom2)

            bot.send_message(callback.message.chat.id, f'Мы заметили, что у вас нет нашей дисконтной карты😞 '
                                                       f'Предлагаем вам создать ее, чтобы в дальнейшем приобретать наш товар по более выгодной цене)',
                             reply_markup=markup)
        else:
            consultation(callback)
        # bot.delete_message(callback.message.chat.id,callback.message.message_id)
    elif callback.data == 'false_enter':
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Заказ")
        markup1.add(item1)
        bot.send_message(callback.message.chat.id,
                         "Давайте заполним ваши данные заново. Отправьте, пожалуйста, команду <b>/order</b> или нажмите на кнопку <b>Заказ</b>",
                         parse_mode='html', reply_markup=markup1)
    elif callback.data == 'edit_data':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        bottom1 = types.KeyboardButton("ФИО")
        bottom2 = types.KeyboardButton("Номер")
        bottom3 = types.KeyboardButton("Все")
        markup.row(bottom1, bottom2)
        markup.add(bottom3)
        bot.send_message(callback.message.chat.id, f'Выберите, пожалуйста, какие данные поменялись🙃',
                         reply_markup=markup)
    elif callback.data == 'create_card':
        bot.send_message(callback.message.chat.id, "Введите, пожалуйста, свою дату рождения в формате: ДД.ММ.ГГГГ")
        bot.register_next_step_handler(callback.message, lambda message: process_birthday_input(callback, message))
        #checkCard.create_card('cards.xlsx', user_states[callback.message.chat.id]['name'])
        #consultation(callback)
    elif callback.data == 'continue_without_card':
        consultation(callback)
    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Continue....',
                          reply_markup=None)


def process_birthday_input(callback, message):
    user_states[callback.message.chat.id]['birthday'] = message.text.strip()
    if re.match(r'^\d{2}\.\d{2}\.\d{4}$', user_states[callback.message.chat.id]['birthday']):
        bot.send_message(config.manager_id, f'Создать дисконтную карту!\n'
                                            f'Информация о пользователе:\n'
                                            f'Ник пользователя - {callback.message.chat.username}\n'
                                            f'ФИО - {user_states[callback.message.chat.id]['name']}\n'
                                            f'Номер телефона - {user_states[callback.message.chat.id]['phone']}\n'
                                            f'Дата рождения - {user_states[callback.message.chat.id]['birthday']}')
        checkCard.create_card('cards.xlsx',user_states[callback.message.chat.id]['name'], user_states[callback.message.chat.id]['phone'], user_states[callback.message.chat.id]['birthday'])
        consultation(callback)
    else:
        bot.send_message(callback.message.chat.id, f'Неверный формат даты рождения. Введите дату в формате: ДД.ММ.ГГГГ')
        bot.register_next_step_handler(callback.message, lambda message: process_birthday_input(callback, message))

def consultation(callback):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bottom1 = types.KeyboardButton("Консультация")
    bottom2 = types.KeyboardButton("Завершение")
    markup.row(bottom1, bottom2)

    bot.send_message(callback.message.chat.id, "Ваши данные успешно зарегестрированы)")
    bot.send_message(callback.message.chat.id,
                     "Нужна ли вам дополнительная консультация с нашим менеджером по поводу заказа?\n\n"
                     "Выберите <b>Консультация</b>, если нужна\n"
                     "Выберите <b>Завершение</b>, если не нужна", parse_mode='html', reply_markup=markup)


@bot.message_handler()
def info(message):
    if (message.text.lower() == 'привет'):
        bot.send_message(message.chat.id, "😕")
        bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\n "
                                          "Я - <b>электронный сотрудник магазина по продаже тканей</b>, бот созданный чтобы помочь тебе сделать заказ.".format(
            message.from_user, bot.get_me()),
                         parse_mode='html')
    elif (message.text.lower() == 'id'):
        bot.reply_to(message, f'ID: {message.from_user.id}')
    elif (message.text.lower() == 'test'):
        conn = sqlite3.connect('shop.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        products = cur.fetchall()
        info = ''
        for elm in products:
            info += f'name: {elm[1]}, phone: {elm[3]}, id: {elm[2]}, card: {elm[4]}'
            # Отправка сообщения с данными о товаре и фотографией
        bot.send_message(message.chat.id, info)
        cur.close()
        conn.close()
    else:
        bot.reply_to(message, f'Извините, {message.from_user.first_name}, я не умею обрабатывать такие сообщения((')


bot.polling(none_stop=True)