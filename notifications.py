import re
import requests
from config import url_NBU

url = url_NBU
response=requests.get(url).json()

def get_rate_url(currency):
    if (re.match('RUB', currency)):
        currency = 'RUB'
    for curr in response:
        if (currency == str(curr['cc'])):
            rate = str(curr['cc'])
    else:
        rate = '0'
    return rate

def get_rate_string(string):
    currency = string[0:3]
    rate = string[4:len(string)]
    return [currency, rate]

def compare_rates(old_rate,new_rate):
    if(old_rate == new_rate):
        return 0
    else:
        return 1

def read_last_rate(currency):
    with open("currency_rate.txt", 'r') as file:
        while True:
            result = file.readline()
            if(result.startswith(currency) ):
                file.close()
                return result
            if not result:
                break
    result = '-1'
    return  result


def write_new_rate(currency,rate):
    with open("currency_rate.txt", 'a') as file:
        file.write('\n' + str(currency)+':'+str(rate))
        file.close()


def delete_old_rate(currency):
    with open("currency_rate.txt", 'r') as file:
        f = file.readlines()
        f.remove(currency)
        for i in f:
            if not i.isspace():
                i.replace('\n', ' ')
        file.close()
    with open("currency_rate.txt", 'w') as fl:
        fl.writelines(f)
        fl.close()