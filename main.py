# -*- coding: utf-8 -*-

import ast
import calendar
import config
import datetime
import os
import telebot
import logging
# import locale

from flask import Flask, request
from postgres import Postgres
from telebot import types

# seems like heroku dont work with this(
# locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

WEBHOOK_URL = "https://onaft-bot.herokuapp.com/bot"

bot = telebot.TeleBot(config.token)
server = Flask(__name__)

MSG_TODAY           = 'На сегодня'
MSG_TOMORROW        = 'На завтра'
MSG_WEEK            = 'На неделю'
MSG_BACK            = 'Назад'
MSG_CHOOSE_FACULTY  = 'Выберите факультет'
MSG_CHOOSE_GROUP    = 'Выберите группу'  
MSG_DONT_UNDERSTAND = 'Я Вас не понимаю'
MSG_GET_FACKS       = 'Выбрать факультет'
MSG_GET_GROUPS      = 'Выбрать группу'
MSG_PARSE           = '/parser start'
MSG_STATS           = '/stats'
isParserWorking = False

GROUP_A = '🅰'
GROUP_B = '🅱'
GROUP   = '🅾'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('LOGS.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

def log(message):
    print('user[{0}] send: {1}'.format(message.chat.id, message.text))
    db = Postgres().get_instance()

    db.log(message.chat.id, message.text)

@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    """
    Start response only with 3+ symbols 
    """

    logger.info(inline_query.query)
    try:
        db = Postgres().get_instance()
        groups = db.get_group_list()  # get ALL groups
        if not groups:
            exit
        response = []
        i = 1               # making uniq ID for query
        for group in groups:
            if inline_query.query in group[0]:
                response.append(
                    types.InlineQueryResultArticle(
                        i,                               # inline query ID, must be unique!
                        group[0].upper(),                # group name in result list
                        types.InputTextMessageContent(
                            get_today_schedule(group[0]) # today schedule by group_id
                        )
                    )
                )
                i += 1
        bot.answer_inline_query(inline_query.id, response)
    except Exception as e:
        print(e)


# @bot.message_handler(func=lambda m: m.text == MSG_PARSE)
# def reply_on_start_parse(message):
#     if Parser.isFree:
#         Parser.isFree = False
#         Parser.doParse()
#         Parser.isFree = True
#         bot.send_message(
#             message.chat.id,
#             'Start parse...'
#         )
#     else:
#         bot.send_message(
#             message.chat.id,
#             'Parser is very busy...'
#         )


 
def get_today_schedule(group_name):
    """
    Return today schedule for given group
    """
    db = Postgres().get_instance()
    schedule = db.get_schedule_by_group(group_name)

    day = datetime.datetime.today().weekday()  # Monday is 0 and Sunday is 6
    if day == 6:
        day = 0             # if today is sunday -> change to monday
    if schedule:
        lectures = ast.literal_eval(schedule[0][0])
        i = 0
        lecturesCount = int(len(lectures) / 6)
        # 6 - work days in week,
        # len(lectures) - lecture count
        # lecCount/workDays = lecturePerDay (may be different, 5-6)
        messageText = week_days[day] + ' ' + group_name
        print('lecturesCount='+str(lecturesCount))
        print('i='+str(i))
        while i < lecturesCount:
            j = i + (day * lecturesCount)
            print('j='+str(j))
            messageText = messageText + '\n' + \
                lectures[j]['lecture'] + \
                '  ' + lectures[j]['room'] + \
                '  ' + lectures[j]['lecturer']
            print(messageText)
            i = i + 1
        return messageText

@bot.message_handler(func=lambda m: m.text == MSG_GET_GROUPS)
def reply_on_get_groups(message):
    db = Postgres().get_instance()

    # 1 user have defined faculty
    print(message.chat.id)
    f = db.get_user_faculty(message.chat.id)[0][0]
    print(f)
    # 2 user doesnt have predefined faculty - break

    groupList = db.get_groups_by_faculty(f)

    if groupList:
        keyboard = types.ReplyKeyboardMarkup(
            row_width=2,
            resize_keyboard=True, one_time_keyboard=True
        )
        #🅰🅱🆎
        i = 0
        while i < len(groupList):
            # last item case
            if groupList[i] == groupList[-1]:
                keyboard.add(types.KeyboardButton(str(groupList[i][0])))
                break
            # one letter group case
            if groupList[i][0][-1] != 'a' and groupList[i][0][-1] != 'b':
                keyboard.add(types.KeyboardButton(str(groupList[i][0])))
                i += 1
                continue
            # two letter group case
            keyboard.add(
                types.KeyboardButton(str(groupList[i   ][0])),
                types.KeyboardButton(str(groupList[i + 1][0]))
            )
            i += 2
        bot.send_message(
            message.chat.id,
            MSG_CHOOSE_GROUP,
            reply_markup=keyboard
        )
        return

@bot.message_handler(func=lambda m: m.text == MSG_GET_FACKS)
def reply_on_get_facks(message):
    db = Postgres().get_instance()
    facultiesList = db.get_faculties()

    if facultiesList:
        keyboard = types.ReplyKeyboardMarkup(
            row_width=1,
            resize_keyboard=True, one_time_keyboard=True
        )
        for faculty in facultiesList:
            keyboard.add(types.KeyboardButton(faculty[0]))

        bot.send_message(
            message.chat.id,
            MSG_CHOOSE_FACULTY,
            reply_markup=keyboard
        )

@bot.message_handler(commands=['start'])
def reply_on_start(message):
    """
    Reply on /start command
    """
    # log(message)
    db = Postgres().get_instance()
    if not db.get_user(message.chat.id):  # Create new user if not exists
        db.add_user(message.chat.id)
        print('[Info] New user was created ' +
              str(db.get_user(message.chat.id)))
    
    reply_on_get_facks(message)


@bot.message_handler(func=lambda m: m.text == MSG_TODAY or m.text == MSG_TOMORROW)
def reply_on_today_tomorrow(message):
    """
    Reply on both MSG_TODAY and MSG_TOMORROW
    """

    print('[info] user ' + str(message.chat.id) + ' press today/tomorow')
    oneDayMargin = 0
    if message.text.lower() == MSG_TOMORROW.lower():
        oneDayMargin = 1                            # if pressed tomorrow, select +1 day

    db = Postgres()
    schedule = db.get_schedule(message.chat.id)
    if not schedule:
        bot.send_message(message.chat.id, MSG_DONT_UNDERSTAND)
        return
    
    day = datetime.datetime.today().weekday() + oneDayMargin
    
    if day == 6 or day == 7:                        # calendar accept 0..6
        day = 0                                     # if today is sunday -> change to monday
    if schedule:
        lectures = ast.literal_eval(schedule[0][0])
        
        """
        len(lectures) is a
        lectures count in week, divide that number by work days count - and we gat a 
        count lectures per Okday
        """

        lecturesCount = int(len(lectures) / 6)
        messageText = '*{0}*'.format(week_days[day])
        i = 0
        while i < lecturesCount:
            j = i + (day * lecturesCount)
            messageText = '{text}\n{item}'.format(
                text = messageText,
                item='* - ' + lectures[j]['lecture'] + '*\n  '+lectures[j]['lecturer']+ '\n  '+lectures[j]['room']
            )
            i += 1
        bot.send_message(message.chat.id, messageText, parse_mode="markdown")
    else:
        bot.send_message(message.chat.id, MSG_DONT_UNDERSTAND)


@bot.message_handler(func=lambda m: m.text == MSG_WEEK)
def reply_on_next(message):
    """
    Reply on MSG_WEEK
    """

    print('[info] user ' + str(message.chat.id) + ' press week')
    db = Postgres().get_instance()
    schedule = db.get_schedule(message.chat.id)
    if not schedule:
        bot.send_message(message.chat.id, MSG_DONT_UNDERSTAND)
        return
    toDay = datetime.datetime.today().weekday()  # Monday is 0 and Sunday is 6

    if schedule:
        lectures = ast.literal_eval(schedule[0][0])
        for day in range(0, 6):
            i = 0
            # 6 - work days in week, len(lectures) - lecture count
            lecturesCount = int(len(lectures) / 6)
            # lecCount/workDays = lecturePerDay (may be different)
            messageText = '\n*{day}*'.format(day=week_days[day])

            while i < lecturesCount:
                if (i + (day * lecturesCount) - 1) < len(lectures):
                    j = i + (day * lecturesCount)
                    messageText = '{text}\n{item}'.format(
                        text = messageText,
                        item='* - ' + lectures[j]['lecture'] + '*\n  ' +
                        lectures[j]['lecturer'] + '\n  '+lectures[j]['room']
                    )

                else:
                    messageText = '{text}\n_-_'.format(text = messageText) 
                i = i + 1
            bot.send_message(message.chat.id, messageText,
                             parse_mode="markdown")
    else:
        bot.send_message(message.chat.id, MSG_DONT_UNDERSTAND)


@bot.message_handler(func=lambda m: m.text == MSG_STATS)
def reply_on_stats(message):
    logger.info(str(message.chat.id) + ' send ' + message.text)
    db = Postgres().get_instance()
    statistics = """
                    Зарегистрированых пользователей: {0}
                    Сообщений Всего: {1}""".format(
                        db.getUsersCount(),
                        db.getUsage()
                    )
    
    bot.send_message(message.chat.id, statistics)

@bot.message_handler(content_types=['text'])
def reply_on_next_text(message):
    """
    Reply on any text
    """
    # log(message)
    logger.info(str(message.chat.id) + ' send ' + message.text)
    print('[info] user ' + str(message.chat.id) + ' send ' + message.text)
    db = Postgres().get_instance()

    groupList = db.get_groups_by_faculty(message.text)

    if groupList:
        db.update_user_faculty(message.chat.id, message.text)

        keyboard = types.ReplyKeyboardMarkup(
            row_width=2,
            resize_keyboard=True, one_time_keyboard=True
        )
        #🅰🅱🆎
        i = 0
        while i < len(groupList):
            # last item case
            if groupList[i] == groupList[-1]:
                keyboard.add(types.KeyboardButton(str(groupList[i][0])))
                break
            # one letter group case
            if groupList[i][0][-1] != 'a' and groupList[i][0][-1] != 'b':
                keyboard.add(types.KeyboardButton(str(groupList[i][0])))
                i += 1
                continue
            # two letter group case
            keyboard.add(
                types.KeyboardButton(str(groupList[i][0])),
                types.KeyboardButton(str(groupList[i + 1][0]))
            )
            i += 2
        bot.send_message(
            message.chat.id,
            MSG_CHOOSE_GROUP,
            reply_markup=keyboard
        )
        return

    schedule = db.get_schedule_by_group(message.text)

    if schedule:
        db.update_user(message.chat.id, message.text)
        keyboard = types.ReplyKeyboardMarkup(
            row_width=2, resize_keyboard=True, one_time_keyboard=False)
        keyboard.add(MSG_TODAY)
        keyboard.add(MSG_TOMORROW)
        keyboard.add(MSG_WEEK)
        keyboard.add(MSG_GET_FACKS, MSG_GET_GROUPS)
        # keyboard.add(MSG_TODAY, MSG_TOMORROW, MSG_WEEK)
        bot.send_message(message.chat.id, 'Готово! (что бы выбрать группу/факультет заново, отправьте /start)', reply_markup=keyboard)
    else:
        keyboardAd = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(
            text="onaft.edu.ua", url="https://www.onaft.edu.ua/ru/")
        keyboardAd.add(url_button)
        bot.send_message(message.chat.id, MSG_DONT_UNDERSTAND, reply_markup=keyboardAd)


@server.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))]
    )
    return "You're quite close", 200

@server.route("/update", methods=['GET', 'POST'])
def getUpdate():
    result = 'That what I get:'
    if request.args.get("faculty"):
        result = result + request.args.get("faculty")
    if request.args.get("group"):
        result = result + request.args.get("group")
    return result, 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    return "There is nothing what you are looking for", 200


server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
server = Flask(__name__)
