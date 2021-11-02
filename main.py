import config
import requests
import ccy
import re
import logging
from datetime import datetime

import os
import sql
from sql import SQLl

import  asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text

from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import notifications

class Date(StatesGroup):
    dt = State()

class Crr(StatesGroup):
    cur = State()

class Archive(StatesGroup):
    cur = State()

class get_Notifications(StatesGroup):
    cur = State()

class calc_data(StatesGroup):
    cur = State()
    number = State()

class schedule_data(StatesGroup):
    cur = State()
    time = State()


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot,storage=storage)
db = SQLl('db.db')
response_PB = requests.get(config.url_PB).json()
response_Mono = requests.get(config.url_Mono).json()
response_NBU = requests.get(config.url_NBU).json()

#Отмена
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('ОК')


@dp.message_handler(commands = ['start','help'])
async def welcome(message: types.Message):
    await message.answer("Введите команду :"
                         "\n/menu - предоставляет пользователю меню выбора доступных функций"
                         "\n/help - справка о боте и доступных командах"
                         "\n/crt - узнать нынешний курс валют"
                         "\n/cbd - узнать курс валюты по дате"
                         "\n/ntf - подписаться на уведомления об изменении валюты"
                         "\n/calc - калькулятор валют"
                         "\n/schedule - подписаться на уведомления о курсе валюты по расписанию"
                         "\n/unsub - отписаться от уведомлений об изменении валюты"
                         "\n/unssc - отписаться от уведомлений о курсе валюты по расписанию")

#Основное меню
@dp.message_handler(commands = ['menu'])
async def menu(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('Нынешний курс валют')
    itembtn2 = types.KeyboardButton('Курс валют по дате')
    itembtn3 = types.KeyboardButton('Уведомления об измененнии курса')
    itembtn4 = types.KeyboardButton('Уведомления по расписанию')
    itembtn5 = types.KeyboardButton('Калькулятор')
    markup.add(itembtn1, itembtn2, itembtn3,itembtn4,itembtn5)
    await message.answer("Выберите действие, которое хотите совершить или напишите команду", reply_markup=markup)

#Выбор валюты
@dp.message_handler(commands = ['current_currency_rate','crt'])
@dp.message_handler(Text(equals="Нынешний курс валют"))
async def current_rate(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('USD')
    itembtn2 = types.KeyboardButton('EUR')
    itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
    itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
    markup.add(itembtn1, itembtn2, itembtn3,itembtn4)
    await message.answer('Узнать наличный курс ', reply_markup=markup)
    await Crr.cur.set()

@dp.message_handler(state=Crr.cur)
async def save_currency(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardRemove(selective=False)
    curr = str(message.text)
    await state.finish()
    if(curr.isalpha() and curr.isupper() and len(curr) == 3):
        await get_currency_rate_PB(message)
        await get_currency_rate_Mono(message)
        await get_currency_rate_NBU(message)
    else:
        await message.answer("Вы некорректно ввели валюту. Код валюты состоит из трех заглавных букв латинского алфавита.",reply_markup=markup)


#Курс МоноБанк
async def get_currency_rate_Mono(message: types.Message):
            markup = types.ReplyKeyboardRemove(selective=False)
#        try:
            if (re.match('RUB', message.text) or re.match('RUR', message.text)):
                currencyCode = 643
            else:
                try:
                    currencyName = ccy.currency(message.text)
                    currencyCode = currencyName.isonumber
                    for currency in response_Mono:
                        if (int(currencyCode) == int(currency['currencyCodeA']) and int(currency['currencyCodeB']) == 980):
                            await message.answer(bot_reply('МоноБанк', currency['rateBuy'], currency['rateSell']),
                                                 reply_markup=markup)
                            break

                except Exception as e:
                    await message.answer(
                        'Вы ввели некорректную или недостуную для Монобанка валюту! Попробуйте ввести еще раз или воспользуйтесь меню.')

#Курс ПриватБанка
async def get_currency_rate_PB(message: types.Message):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUR', message.text)):
            message.text='RUR'
        for currency in response_PB:
            if (message.text == currency['ccy']):
                await message.answer(bot_reply('ПриватБанк',currency['buy'], currency['sale']),reply_markup=markup)
    except Exception as e:
        await message.answer('Вы ввели некорректную или недостуную для ПриватБанка валюту! Попробуйте ввести еще раз или воспользуйтесь меню.')


#Курс НБУ
async def get_currency_rate_NBU(message: types.Message):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUB', message.text)):
            message.text='RUB'
        for currency in response_NBU:
            if (message.text == str(currency['cc'])):
                await message.answer(bot_reply('НБУ','', currency['rate']),reply_markup=markup)
    except Exception as e:
        await message.answer('Курс данной валюты недоступен в НБУ ! Попробуйте ввести еще раз или воспользуйтесь меню.')



@dp.message_handler(commands = ['currency_rate_by_date','cbd'])
@dp.message_handler(Text(equals="Курс валют по дате"))
async def get_date(message: types.Message):
    markup = types.ReplyKeyboardRemove(selective=False)
    await message.answer('Ввведите дату (формат даты : 01-01-2020): ', reply_markup=markup)
    await Date.dt.set()


@dp.message_handler(state = Date.dt)
async def rate_date(message: types.Message, state: FSMContext):
    await state.finish()
    if re.match(r'(?<!\d)(?:0?[1-9]|[12][0-9]|3[01])-(?:0?[1-9]|1[0-2])-(?:19[0-9][0-9]|20[012][0-9])(?!\d)',
                    message.text):
            dt = datetime.strptime(message.text, "%d-%m-%Y")
            NBU_url = url_to_string(dt)
            global response_PB_archive
            response_PB_archive = requests.get(
                config.url_PB_archive + str(dt.day) + '.' + str(dt.month) + '.' + str(dt.year)).json()
            global response_NBU_archive
            response_NBU_archive = requests.get(config.url_NBU_archive + str(NBU_url) + '&json').json()

            await message.answer("URL - PB: " + config.url_PB_archive + str(dt.day) + '.' + str(dt.month) + '.' + str(
                dt.year) + "\nURL - NBU:" + config.url_NBU_archive + str(NBU_url) + '&json')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            itembtn1 = types.KeyboardButton('USD')
            itembtn2 = types.KeyboardButton('EUR')
            itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
            itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
            markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
            await message.answer("Узнать наличный курс ", reply_markup=markup)
            await Archive.cur.set()
    else:
        await message.answer(message, "Вы не верно ввели дату")


@dp.message_handler(state=Archive.cur )
async def get_archive(message: types.Message, state: FSMContext):
    await state.finish()
    markup = types.ReplyKeyboardRemove(selective=False)
    curr = str(message.text)
    if (curr.isalpha() and curr.isupper() and len(curr) == 3):
        await get_NBU_archive(message)
        await get_PB_archive(message)
    else:
        await message.answer(
            "Вы некорректно ввели валюту. Код валюты состоит из трех заглавных букв латинского алфавита.",
            reply_markup=markup)


async def get_NBU_archive(message: types.Message):
    markup = types.ReplyKeyboardRemove(selective=False)
    for currency in response_NBU_archive:
        if (message.text == str(currency['cc'])):
            await message.answer(bot_reply('НБУ', '', currency['rate']),reply_markup=markup)
            break
    else:
        await message.answer(message.chat.id,'Вы не верно ввели валюту',reply_markup=markup)


async def get_PB_archive(message: types.Message):
        markup = types.ReplyKeyboardRemove(selective=False)
        if (re.match('RUR', message.text)):
            message.text = 'RUR'
        del response_PB_archive['exchangeRate'][0]
        for currency in response_PB_archive['exchangeRate']:
            if (message.text == currency ['currency']):
                await message.answer(bot_reply('ПриватБанк', currency['purchaseRate'], currency['saleRate']),reply_markup=markup)
                break
        else:
            await message.answer('Вы не верно ввели валюту/курс ПриватБанка сходится с курсом НБУ',reply_markup=markup)

# Уведомления об изменении курса валют
@dp.message_handler(commands=['ntf'])
@dp.message_handler(Text(equals="Уведомления об измененнии курса"))
async def set_Update(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('USD')
    itembtn2 = types.KeyboardButton('EUR')
    itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
    itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    await message.answer("выберите курс валюты, об изменениях которой хотите получать уведомления ", reply_markup=markup)
    await get_Notifications.cur.set()

@dp.message_handler(state=get_Notifications.cur )
async def get_Update_currency(message: types.Message, state: FSMContext):
    currency_notifications = message.text
    markup = types.ReplyKeyboardRemove(selective=False)
    await state.finish()
    curr = str(message.text)
    if (curr.isalpha() and curr.isupper() and len(curr) == 3):
        await subscribe(message,currency_notifications)
    else:
        await message.answer(
            "Вы некорректно ввели валюту. Код валюты состоит из трех заглавных букв латинского алфавита.",
            reply_markup=markup)

# Калькулятор
@dp.message_handler(commands=['calc'])
@dp.message_handler(Text(equals="Калькулятор"))
async def get_calc_curr(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('USD')
    itembtn2 = types.KeyboardButton('EUR')
    itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
    itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    await message.answer("Выберите или введите валюту, в которую хотите перевести: ",reply_markup=markup)
    await calc_data.cur.set()

@dp.message_handler(state=calc_data.cur )
async def get_calc_number(message: types.Message, state: FSMContext):
    await state.update_data(cur=message.text)
    markup = types.ReplyKeyboardRemove(selective=False)
    await message.answer("Введите сумму, которую хотите перевести : ", reply_markup=markup)
    await calc_data.number.set()


@dp.message_handler(state=calc_data.number )
async def calc(message: types.Message, state: FSMContext):
    if (is_int(message.text)):
        calc_number = int(message.text)
        data = await state.get_data()
        calc_currency = data.get("cur")
        del data
        await state.finish()
        if (re.match('RUB', calc_currency)):
            calc_currency = 'RUB'
        for currency in response_NBU:
            if (calc_currency == str(currency['cc'])):
                nbu_rate = int (currency['rate'])
                calc_res = nbu_rate *  calc_number
                await message.answer(str(calc_number) + " гривен = " + str(calc_res) + ' ' + str(calc_currency) + "\n")
                calc_res = calc_number / nbu_rate
                await message.answer(str(calc_number) + ' ' + str(calc_currency)+ ' = '  + str(calc_res) +" гривен\n")
                break
        else:
            await message.answer("Введенная Вами валюта не найдена в базе.")
    else:
        await message.answer("Некорректный ввод числав.")
@dp.message_handler(commands=['schedule'])
@dp.message_handler(Text(equals="Уведомления по расписанию"))
async def set_schedule_currency(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('USD')
    itembtn2 = types.KeyboardButton('EUR')
    itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
    itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    await message.answer("Выберите валюту: ", reply_markup=markup)
    await schedule_data.cur.set()

@dp.message_handler(state=schedule_data.cur)
async def set_schedule_time(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardRemove(selective=False)
    await message.answer("Введите время, в которое Вы хотите получать уведомления: ", reply_markup=markup)
    await state.update_data(cur=message.text)
    await schedule_data.time.set()

@dp.message_handler(state=schedule_data.time)
async def set_schedule(message: types.Message, state: FSMContext):
    get_time_sc = message.text
    data = await state.get_data()
    calc_currency = str(data.get("cur"))
    del data
    await state.finish()
    if (calc_currency.isalpha() and calc_currency.isupper() and len(calc_currency) == 3):
        await sschedule(message,calc_currency,get_time_sc)
    else:
        await message.answer(
            "Вы некорректно ввели валюту. Код валюты состоит из трех заглавных букв латинского алфавита.")

async def schedule(wait_for):
    if (os.path.exists("db.db")):
        while True:
            await asyncio.sleep(wait_for)
            subscriptions = db.get_subscriptions()
            for ntf in subscriptions:
                if (ntf[3]):
                    now = datetime.now()
                    time_db = ntf[5]
                    minutes = str(time_db[3])+str(time_db[4])
                    hour = str(time_db[0]) + str(time_db[1])
                    if(int(now.minute) == int(minutes) and int(now.hour) == int(hour)):
                        currency_notifications = ntf[6]
                        for currency in response_NBU:
                            if (currency_notifications == str(currency['cc'])):
                                await bot.send_message(ntf[1],bot_reply('НБУ', '', currency['rate']))
                                del now,minutes,hour
                                break

async def get_Update(wait_for):
    if (os.path.exists("db.db")):
        while True:
            await asyncio.sleep(wait_for)
            subscriptions = db.get_subscriptions()
            for ntf in subscriptions:
                if(ntf[2]):
                    currency_notifications = ntf[4]
                    data = requests.get(config.url_NBU).json()
                    rate = 0
                    if (re.match('RUR', currency_notifications)):
                        currency_notifications = 'RUB'
                    for crr in data:
                        if (currency_notifications == str(crr['cc'])):
                            rate = crr['rate']
                            break
                    if(rate == 0):
                        await bot.send_message(s[1],"Error")
                        break
                    old_rate = notifications.read_last_rate(currency_notifications)
                    if (old_rate == '-1'):
                        new_rate = rate
                        notifications.write_new_rate(currency_notifications, rate)
                        notification = "Нынешний курс " + str(currency_notifications) + " :" + str(rate)
                        del new_rate
                        await bot.send_message(ntf[1], notification)
                        break
                    if (old_rate == ""):
                        new_rate = rate
                        notifications.write_new_rate(currency_notifications, rate)
                        notification = "Нынешний курс " + str(currency_notifications) + " :" + str(rate)
                        del new_rate
                        for s in subscriptions:
                            await bot.send_message(s[1], notification)
                    else:
                        print_from_file = notifications.get_rate_string(old_rate)
                        old_rate = print_from_file[1]
                        old_currency = print_from_file[0]
                        if (float(old_rate) != float(rate)):
                            delete = old_currency + ':' + str(old_rate)
                            notifications.delete_old_rate(delete)
                            notifications.write_new_rate(currency_notifications, rate)
                            old_rate = print_from_file[1]
                            old_currency = print_from_file[0]
                            print_from_file = notifications.read_last_rate(currency_notifications)
                            print_from_file = notifications.get_rate_string(print_from_file)
                            new_rate = print_from_file[1]
                            notification = "Старый курс " + str(old_currency) + " :" + str(old_rate) + "\nНовый курс : " + str(new_rate)
                            del old_currency, old_rate, print_from_file, new_rate
                            for s in subscriptions:
                                await bot.send_message(s[1], notification)

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


#добавление 0 перед днем/месяцем < 10
def date_to_string(date):
    text=''
    if int(date.hour) < 10:
        text += '0' + str(date.hour)
    else:
        text +=str(date.hour)
    if int(date.minute) < 10:
        text += ':0' + str(date.minute)
    else:
        text +=':' + str(date.minute)
    return text

#подписаться
@dp.message_handler(commands=['sub'])
async def subscribe(message: types.Message,currency):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id,currency)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id,currency,True)
    markup = types.ReplyKeyboardRemove(selective=False)
    await message.answer("Вы успешно подписались на уведомления!",reply_markup=markup)
#отписаться
@dp.message_handler(commands=['unsub'])
async def unsubscribe(message: types.Message):
    markup = types.ReplyKeyboardRemove(selective=False)
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы не подписаны.",reply_markup=markup)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы отписаны от уведомлений.",reply_markup=markup)

#подписаться
@dp.message_handler(commands=['ssc'])
async def sschedule(message: types.Message,currency,time):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        db.add_schdule(message.from_user.id,currency,time)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_schedule(message.from_user.id,currency,time,True)
    markup = types.ReplyKeyboardRemove(selective=False)
    await message.answer("Вы успешно подписались на уведомления по расписанию!",reply_markup=markup)
#отписаться
@dp.message_handler(commands=['unsc'])
async def unschedule(message: types.Message):
    markup = types.ReplyKeyboardRemove(selective=False)
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_schdule(message.from_user.id, False)
        await message.answer("Вы не подписаны.",reply_markup=markup)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_schedule(message.from_user.id, False)
        await message.answer("Вы отписаны от уведомлений по расписанию.",reply_markup=markup)

# проверка на число
def is_int(str):
    try:
        int(str)
        return True
    except ValueError:
        return False


def main():
    loop = asyncio.get_event_loop()
    loop.create_task(get_Update(10))
    loop.create_task(schedule(10))

    executor.start_polling(dispatcher=dp)

if __name__ == '__main__':
    main()