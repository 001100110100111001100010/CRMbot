#api
import telebot
from telebot import types
import requests as req
import socket

#sys
import time
import datetime
from re import *
import sqlite3
import random

class Bot_tools:
    
    def send_app(ids):
        # Ids its a string  
        API_KEY = "I10f2P4i3M78e2P0S4Z6A3h5t686T6"
        IP = "213.139.211.11"
        # параметры: API_KEY(содержит ключ для доступа к qpi сервера);
        #            alert_to(параметр для вызова api функции, которая принимает telegram_id)
        headers = { 'type' : 'incoming', 'API_KEY' : API_KEY, 'alert_to' : ids} 
        URL = 'http://{0}/Receive/BotEntrance?'.format(IP)
        
        resp = req.get(URL, headers)
        
        return resp.content
        
    def call_to(sender, login, password, tel):
        msg = 'Заявка Заявка Заявка Заявка'
        url = 'https://smsc.ru/sys/send.php?'
        parms = 'login={0}&psw={1}&phones={2}&mes={3}&sender={4}&call=1'.format(login, password, tel, msg, sender)
        req.get(url+parms)    
            
        time.sleep(1)
        
    def tel_parser(data):
    
        def check_goal(goal):
            if (goal[0] == '7') and (len(goal) == 11):
                return True
            elif (goal[0] == '8') and (len(goal) == 11):
                return True
            elif (goal[0] == '9') and (len(goal) == 10):
                return True
            else: return False
    
        tels = findall('\d{10}',data)+findall('\d{11}',data)+findall('\d{12}',data)
        tels = [i for i in tels if i[0] in '+789']
        tels = [i for i in tels if check_goal(i) == True]
        if tels != []:
            return tels
        else:            
            return 'Incorrect / Not found'    

    def create_auth_token():
        AuthToken = datetime.datetime.now()
        AuthToken = '{0}{1}{2}'.format(AuthToken.day,AuthToken.microsecond,AuthToken.year)
        seps = 'qPOLMKIJNAQ-=:wertyuioUHBYGWpl-=:kjhgfdsVT-=:FCRDXESZazxcvbnm-_=:' 
        key = ''.join([random.choice(seps)+random.choice('0123456789') for i in range(17)])+AuthToken
        with open('auth_token.py','w') as f:
            f.write("key='{}'".format(key))
        return key
    
    def alert_to():
        sock = socket.socket()
        sock.connect(('localhost', 3033))
        sock.send(b'hello')
        sock.close()    
        