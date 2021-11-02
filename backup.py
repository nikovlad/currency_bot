import config
import telebot
import requests
from telebot import types
import ccy
import re
from datetime import datetime
import sql
from sql import SQLl

bot = telebot.TeleBot(config.BOT_TOKEN)

#мб потом в отдельную функцию
response_PB = requests.get(config.url_PB).json()
response_Mono = requests.get(config.url_Mono).json()
response_NBU = requests.get(config.url_NBU).json()


@bot.message_handler(commands=['subscribe'])
def subscribe(message: types.Message):
    if (not bot.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        bot.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        bot.update_subscription(message.from_user.id, True)

    message.answer("Вы успешно подписались на уведомления!")



@bot.message_handler(commands = ['start','help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('Нынешний курс валют')
    itembtn2 = types.KeyboardButton('Курс валют по дате')
    itembtn3 = types.KeyboardButton('Уведомления об измененнии курса')
    itembtn4 = types.KeyboardButton('Уведомления по расписанию')
    itembtn5 = types.KeyboardButton('Калькулятор')
    markup.add(itembtn1, itembtn2, itembtn3,itembtn4,itembtn5)
    msg = bot.send_message(message.chat.id,
                           "Выберите действие, которое хотите совершить или напишите команду", reply_markup=markup)

    # Команда отписки


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message: types.Message):
    if (not bot.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        bot.add_subscriber(message.from_user.id, False)
        message.answer("Вы не подписаны.")
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        bot.update_subscription(message.from_user.id, False)
        message.answer("Вы отписаны от уведомлений.")


@bot.message_handler(content_types = ['text'])
def menu(message):
    if(message.text == 'Нынешний курс валют'):
        current_rate(message)
    elif(message.text == 'Курс валют по дате'):
        get_date(message)
    elif(message.text == '/sub'):
        subscribe(message)
    else:
        bot.reply_to(message,'Введите команду')


@bot.message_handler(commands = ['currency_rate_by_date','cbd'])
def get_date(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    msg = bot.send_message(message.chat.id, 'Ввведите дату (формат даты : 01-01-2020): ', reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(msg, rate_by_date)

#получаем json
def rate_by_date(message):
    if re.match(r'(?<!\d)(?:0?[1-9]|[12][0-9]|3[01])-(?:0?[1-9]|1[0-2])-(?:19[0-9][0-9]|20[012][0-9])(?!\d)', message.text):
       dt = datetime.strptime(message.text, "%d-%m-%Y")

       NBU_url = url_to_string(dt)
       global response_PB_archive
       response_PB_archive = requests.get(config.url_PB_archive + str(dt.day) + '.' + str(dt.month) + '.' + str(dt.year)).json()
       global response_NBU_archive
       response_NBU_archive = requests.get(config.url_NBU_archive + str(NBU_url) + '&json').json()

       msg = bot.send_message(message.chat.id, "URL - PB: " + config.url_PB_archive+str(dt.day)+'.'+str(dt.month)+'.'+str(dt.year) + "\nURL - NBU:" + config.url_NBU_archive+str(NBU_url)+'&json')
       markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
       itembtn1 = types.KeyboardButton('USD')
       itembtn2 = types.KeyboardButton('EUR')
       itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
       itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
       markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
       msg = bot.send_message(message.chat.id,
                              "Узнать наличный курс ", reply_markup=markup)
       bot.register_next_step_handler(msg, get_NBU_archive)

       bot.register_next_step_handler(msg, get_PB_archive)

    else:
        bot.reply_to(message, "Вы не верно ввели дату")




def get_NBU_archive(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    for currency in response_NBU_archive:
        if (message.text == str(currency['cc'])):
            bot.send_message(message.chat.id, bot_reply('НБУ', '', currency['rate']),
                             reply_markup=markup, parse_mode="Markdown")
            break
    else:
        bot.send_message(message.chat.id,bot_reply('Вы не верно ввели валюту',reply_markup=markup, parse_mode="Markdown"))


def get_PB_archive(message):
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUR', message.text)):
            message.text = 'RUR'
        del response_PB_archive['exchangeRate'][0]
        for currency in response_PB_archive['exchangeRate']:
            if (message.text == currency ['currency']):
                bot.send_message(message.chat.id, bot_reply('ПриватБанк', currency['purchaseRate'], currency['saleRate']),
                                 reply_markup=markup, parse_mode="Markdown")
                break
        else:
            bot.send_message(message.chat.id,bot_reply('Вы не верно ввели валюту/курс ПриватБанка сходится с курсом НБУ',reply_markup=markup, parse_mode="Markdown"))

@bot.message_handler(commands = ['current_currency_rate','crt'])
def current_rate(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('USD')
    itembtn2 = types.KeyboardButton('EUR')
    itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
    itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
    markup.add(itembtn1, itembtn2, itembtn3,itembtn4)
    msg = bot.send_message(message.chat.id,
                           "Узнать наличный курс ", reply_markup=markup)
    bot.register_next_step_handler(msg, get_currency_rate_PB)
    bot.register_next_step_handler(msg, get_currency_rate_Mono)
    bot.register_next_step_handler(msg, get_currency_rate_NBU)



#Курс Монобанка
def get_currency_rate_Mono(message):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUB', message.text)  or  re.match('RUR', message.text)) :
            currencyCode = 643
        else:
            currencyName = ccy.currency(message.text)
            currencyCode = currencyName.isonumber

        for currency in response_Mono:
            if (int(currencyCode) == int(currency['currencyCodeA']) and int(currency['currencyCodeB']) == 980):
                bot.send_message(message.chat.id, bot_reply('МоноБанк',currency['rateBuy'], currency['rateSell']),
                                 reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, 'Вы ввели некорректную или недостуную для МоноБанка валюту! Попробуйте ввести еще раз или воспользуйтесь меню.')

#Курс ПриватБанка
def get_currency_rate_PB(message):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUR', message.text)):
            message.text='RUR'

        for currency in response_PB:
            if (message.text == currency['ccy']):
                bot.send_message(message.chat.id, bot_reply('ПриватБанк',currency['buy'], currency['sale']),
                                 reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, 'Вы ввели некорректную или недостуную для ПриватБанка валюту! Попробуйте ввести еще раз или воспользуйтесь меню.')

#Курс НБУ
def get_currency_rate_NBU(message):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUB', message.text)):
            message.text='RUB'
        for currency in response_NBU:
            if (message.text == str(currency['cc'])):
                bot.send_message(message.chat.id, bot_reply('НБУ','', currency['rate']),
                                 reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, 'Курс данной валюты недоступен в НБУ ! Попробуйте ввести еще раз или воспользуйтесь меню.')

#Вывод информации
def bot_reply(bank,buy, sale):
    if(bank=="НБУ"):
        return str(bank) + "\n*Курс валюты:* " + str(sale)
    else:
        return str(bank) + " : \n*Курс покупки:* " + str(buy) + "\n*Курс продажи:* " + str(sale)



#добавление 0 перед днем/месяцем < 10
def url_to_string(date):
    text =''+ str(date.year)
    if int(date.month) < 10:
        text += '0' + str(date.month)
    else:
        text +=str(date.month)
    if int(date.day) < 10:
        text += '0' + str(date.day)
    else:
        text += str(date.day)
    return text

if __name__ == '__main__':
    bot.polling(none_stop=True)


"""
import time
import schedule

def send_message():
    bot.send_message(370921204, 'Hello')


schedule_time = message.text

schedule.every().day.at("schedule_time").do(send_message())
while True:
    schedule.run_pending()
    time.sleep(1)
"""