

#получаем json
async def rate_by_date(message: types.Message):
    if re.match(r'(?<!\d)(?:0?[1-9]|[12][0-9]|3[01])-(?:0?[1-9]|1[0-2])-(?:19[0-9][0-9]|20[012][0-9])(?!\d)', message.text):
       dt = datetime.strptime(message.text, "%d-%m-%Y")

       NBU_url = url_to_string(dt)
       global response_PB_archive
       response_PB_archive = requests.get(config.url_PB_archive + str(dt.day) + '.' + str(dt.month) + '.' + str(dt.year)).json()
       global response_NBU_archive
       response_NBU_archive = requests.get(config.url_NBU_archive + str(NBU_url) + '&json').json()

       await message.answer("URL - PB: " + config.url_PB_archive+str(dt.day)+'.'+str(dt.month)+'.'+str(dt.year) + "\nURL - NBU:" + config.url_NBU_archive+str(NBU_url)+'&json')
       markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
       itembtn1 = types.KeyboardButton('USD')
       itembtn2 = types.KeyboardButton('EUR')
       itembtn3 = types.KeyboardButton('RUR (курс рубля в ПриватБанке)')
       itembtn4 = types.KeyboardButton('RUB (курс рубля в НБУ)')
       markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
       await message.answer("Узнать наличный курс ", reply_markup=markup)
       await get_NBU_archive(message)
       await get_PB_archive(message)

    else:
        await message.answer(message, "Вы не верно ввели дату")




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





#Курс Монобанка
async def get_currency_rate_Mono(message: types.Message):

        if (re.match('RUB', message.text)  or  re.match('RUR', message.text)) :
            currencyCode = 643
        else:
            currencyName = ccy.currency(message.text)
            currencyCode = currencyName.isonumber

        for currency in response_Mono:
            if (int(currencyCode) == int(currency['currencyCodeA']) and int(currency['currencyCodeB']) == 980):
                await message.answer(bot_reply('МоноБанк',currency['rateBuy'], currency['rateSell']),  reply_markup=markup)


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

#Вывод информации
async def bot_reply(bank,buy, sale):
    if(bank=="НБУ"):
        return str(bank) + "\n*Курс валюты:* " + str(sale)
    else:
        return str(bank) + " : \n*Курс покупки:* " + str(buy) + "\n*Курс продажи:* " + str(sale)

#подписаться
@dp.message_handler(commands=['sub'])
async def subscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, True)

    await message.answer("Вы успешно подписались на уведомления!")
#отписаться
@dp.message_handler(commands=['unsub'])
async def unsubscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы не подписаны.")
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы отписаны от уведомлений.")


#добавление 0 перед днем/месяцем < 10
async def url_to_string(date):
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


def main():
    executor.start_polling(dispatcher=dp)

if __name__ == '__main__':
    main()


"""
import time
import schedule

async def answer():
    bot.answer(370921204, 'Hello')


schedule_time = message.text

schedule.every().day.at("schedule_time").do(answer())
while True:
    schedule.run_pending()
    time.sleep(1)
"""

