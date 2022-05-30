# api
import telebot
from telebot import types
import requests as req
import socket

# sys
import time
import datetime
from re import *
import sqlite3
import random
import xlsxwriter

# modules
from tools import *
from config import *
    
#  внутренние методы
class inside_actions:
    
    def __init__(self, token):
        self.token = token
        bot = telebot.TeleBot(self.token)
        self.bot = bot
    
    # создание таблицы
    def create_db(self, conn, key):
        CURSOR = conn.cursor()
        CURSOR.execute("CREATE TABLE reg_key (id int);")
        CURSOR.execute("INSERT INTO reg_key (id) VALUES (?);", (key,))
        CURSOR.execute("CREATE TABLE mngrs (id str, tel str, year int, month int, day int, name str, rank str);")
        CURSOR.execute("CREATE TABLE masters (id str, tel str, year int, month int, day int, name str, rank str);")            
        CURSOR.execute("\
        CREATE TABLE orders (\
        id str, tel str, year int, month int, day int, time str, \
        adress str, problem str, manager str, master str, \
        pay_ma int, pay_me int, price int, raw_price int, \
        detail str, detail_price int);"
        )    
    
    # просмотр сотрудник(-a/-ов)
    def view_empls(self, conn, chat, name=''):
        nm = str(random.randint(1000,10000))
        workbook = xlsxwriter.Workbook('reps//em_{}.xlsx'.format(nm))
        worksheet = workbook.add_worksheet()        
        titles = ['id','тел','год','мес.','день','имя', 'должность']
        worksheet.set_column(0, 1, 25)
        worksheet.set_column(0, 2, 25)
        worksheet.set_column(0, 3, 25)
        worksheet.set_column(0, 4, 25)
        worksheet.set_column(0, 5, 25)
        worksheet.set_column(0, 6, 25)
        worksheet.set_column(0, 7, 25)
        col = 0
        row = 0
        if name == '':            
            CURSOR = conn.cursor()
            CURSOR.execute("SELECT * FROM mngrs ORDER BY name;")
            result1 = CURSOR.fetchall()

            CURSOR.execute("SELECT * FROM masters ORDER BY name;")
            result2 = CURSOR.fetchall()
            CURSOR.close()
            data = result1+result2
        
        elif name != '':
            CURSOR = conn.cursor()
            CURSOR.execute("SELECT * FROM mngrs WHERE name IN (?) ORDER BY name;", (name,))
            result1 = CURSOR.fetchall()

            CURSOR.execute("SELECT * FROM masters WHERE name IN (?) ORDER BY name;", (name,))
            result2 = CURSOR.fetchall()
            CURSOR.close()
            return result1+result2
            
        for j in titles:
            worksheet.write_string(row, col, j)
            col += 1
            
        col2 = 0
        row2 = 1
        for i in data:
            for k in i:
                if k == None:
                    k = '-'
                worksheet.write_string(row2,col2, str(k))
                col2 += 1
            row2 += 1
            col2 = 0            
            
        workbook.close()

        file = 'reps//em_{}.xlsx'.format(nm)
        doc = open(file,"rb")
        del data
        return self.bot.send_document(chat, doc)
            
    # удаление сотрудника из бд
    def delete_emp(self, conn, name, table):
        CURSOR = conn.cursor()
        if table == 'man':
            try:
                CURSOR.execute("SELECT * FROM mngrs WHERE name IN (?) ORDER BY name;", (name,))
                del_empl = CURSOR.fetchall()
                CURSOR.execute("DELETE FROM mngrs WHERE id = ?;", (del_empl[0][0], ))
                conn.commit()
                return 'succ'
            except: return 'Err'    
            finally: CURSOR.close()
            
        if table == 'mas':
            try:
                CURSOR.execute("SELECT * FROM masters WHERE name IN (?) ORDER BY name;", (name,))
                del_empl = CURSOR.fetchall()
                CURSOR.execute("DELETE FROM masters WHERE id = ?;", (del_empl[0][0], ))        
                conn.commit()
                return 'succ'
            except: return 'Err'
            finally: CURSOR.close()
       
        
# шаблоны реакций    
class bot_handlers(inside_actions):
    
    #кэш данных
    pat = {}
    send_users = {}
    stop_mngr = []
    stop_master = []    
    master_ords = {}
    mngr_ords = {}
    send_masters = {}
    
    # проверка на нахождение в бд
    def in_state(self, msg, conn, table=False):
        user_id = str(msg.from_user.id)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM masters WHERE id IN (?) ORDER BY id;", (user_id,))
        result1 = cursor.fetchall()
                    
        cursor.execute("SELECT * FROM mngrs WHERE id IN (?) ORDER BY id;", (user_id,))
        result2 = cursor.fetchall()
        cursor.close()
        if table == False:            
            if result1+result2 == []:
                return False
            else: return True
        else:
            return (result1, result2)
        
    # проверка ключа аутентификации          
    def auth_check(self, msg, key, chat):
        bot = self.bot    
        if msg == key:
            bot.send_message(chat, '✅SUCCESS✅')
            return True
        else: 
            bot.send_message(chat, '❌Не верный ключ❌')         
            return False
            
    # добавление заказа
    def hndl_order(self, conn, phone):
        date = datetime.datetime.now()
        d = '{0}{1}{2}'.format(date.year, date.month, date.day)
        time = '{0}{1}'.format(date.second, date.microsecond)
        id_order = phone.replace('+','')+time
        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (id, tel, year, month, day, time) VALUES (?,?,?,?,?,?);",(id_order, phone, date.year, date.month, date.day, time,))
        conn.commit()
        cursor.close()
        
        return id_order
    
    # рассылка сообщений
    def send_all(self, conn, text, table=None, mrkp=None):
        bot = self.bot
        mesID_hash = {}
        cursor = conn.cursor()
        if table == 'mngr':
            cursor.execute("SELECT id FROM mngrs;")
            users = cursor.fetchall()
            if mrkp != None:
                for chat_id in users:
                    if str(chat_id[0]) not in self.stop_mngr:
                        act = bot.send_message(chat_id[0], text, reply_markup=mrkp)
                        mesID_hash[str(chat_id[0])] = act.id
                return mesID_hash
            else:
                for chat_id in users:
                    if str(chat_id[0]) not in self.stop_mngr:
                        act = bot.send_message(chat_id[0], text)
                        mesID_hash[str(chat_id[0])] = act.id              
                return mesID_hash
                
        elif table == 'master':
            cursor.execute("SELECT id FROM masters;")
            users = cursor.fetchall()
            if mrkp != None:
                for chat_id in users:
                    if str(chat_id[0]) not in self.stop_master:
                        act = bot.send_message(chat_id[0], text, reply_markup=mrkp)
                        mesID_hash[str(chat_id[0])] = act.id
                return mesID_hash
            else:
                for chat_id in users:
                    if str(chat_id[0]) not in self.stop_master:
                        act = bot.send_message(chat_id[0], text)
                        mesID_hash[str(chat_id[0])] = act.id
                return mesID_hash
        else: 
            cursor.execute("SELECT id FROM masters;")
            masters = cursor.fetchall()
            cursor.execute("SELECT id FROM mngrs;")
            mngrs = cursor.fetchall()                
            users = masters+mngrs            
            if mrkp != None:
                for chat_id in users:
                    act = bot.send_message(chat_id[0], text, reply_markup=mrkp)
                    mesID_hash[str(chat_id[0])] = act.id
                return mesID_hash
            else:
                for chat_id in users:
                    act = bot.send_message(chat_id[0], text)
                    mesID_hash[str(chat_id[0])] = act.id
                return mesID_hash

class help_bot(bot_handlers, inside_actions): 
    # кнопка принять
    def order_accept(self, conn, call):
        bot = self.bot
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
            
        data_callback = call.data.split('|')
        time_id = data_callback[2]
        id_ord = data_callback[1]
        if id_ord not in self.mngr_ords.keys():
            bot.send_message(call.message.chat.id, '❌Заявка не существует/была обработана❌')
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        elif int(time.time()) >= (self.mngr_ords[id_ord]['time']+600):
            bot.send_message(call.message.chat.id, '❌Время заявки истекло❌')
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        elif self.mngr_ords[id_ord]['mngr'] != 'null':
            bot.send_message(call.message.chat.id, '❌Кто-то другой уже взял эту заявку❌')
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        else:
            if str(call.from_user.id) in self.send_users.keys():
                del self.send_users[str(call.from_user.id)]
            for id, mes in self.send_users.items():
                bot.edit_message_reply_markup(id, mes, reply_markup=None)
                bot.delete_message(id, mes)
                
            if str(call.from_user.id) in self.stop_mngr:
                pass
            else:
                self.stop_mngr.append(str(call.from_user.id))
                 
            self.mngr_ords[id_ord]['mngr'] = self.in_state(call, conn, True)[1][0][5]
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET manager=? WHERE id=? ;", (str(self.mngr_ords[id_ord]['mngr']), id_ord,))
            conn.commit()
            cursor.close()
            
            telephone = Bot_tools.tel_parser(id_ord)
            bot.send_message(call.message.chat.id, telephone)
            mrkp = types.InlineKeyboardMarkup()
            menu = types.InlineKeyboardButton('заполнить форму', callback_data='quiz'+'|'+id_ord)
            mrkp.add(menu)
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=mrkp)        
    
    # регистрация для менеджеров
    def mngr_reg(self, call, conn):
        bot = self.bot
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
        bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        user = 'n'+str(call.from_user.id)
        if user in self.pat.keys(): 
            
            cursor = conn.cursor()
            cursor.execute('INSERT INTO mngrs (id, tel, year, month, day, name, rank) VALUES \
            (?,?,?,?,?,?,?);', (self.pat[user]['id'], self.pat[user]['phone'], self.pat[user]['year'], self.pat[user]['month'], self.pat[user]['day'], self.pat[user]['name'], 'mngr'))
            conn.commit()
            cursor.close()
            
            bot.send_message(call.message.chat.id, '🎉Вы успешно зарегистрированы🎉')
        else:
            bot.send_message(call.message.chat.id, '❌Время сессии истекло❌')
    
     # регистрация для мастеров
    def master_reg(self, call, conn):
        bot = self.bot
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
        bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        user = 'n'+str(call.from_user.id)
        
        if user in self.pat.keys(): 
            cursor = conn.cursor()
            cursor.execute('INSERT INTO masters (id, tel, year, month, day, name, rank) VALUES \
            (?,?,?,?,?,?,?);', (self.pat[user]['id'], self.pat[user]['phone'], self.pat[user]['year'], self.pat[user]['month'], self.pat[user]['day'], self.pat[user]['name'], 'master'))       
            conn.commit()
            cursor.close()
            
            bot.send_message(call.message.chat.id, '🎉Вы успешно зарегистрированы🎉')
        else:
            bot.send_message(call.message.chat.id, '❌Время сессии истекло❌')
            
    def alarm(self, msg, conn, sender, log, pas):
        phone = Bot_tools.tel_parser(msg.text)[0]
        if phone == 'Incorrect / Not found':
            return None
        else:
            id_ord = self.hndl_order(conn,phone)
            
            cursor = conn.cursor()
            cursor.execute("SELECT id, tel FROM mngrs;")
            users = cursor.fetchall()
            users = [str(i[1]) for i in users if str(i[0]) not in self.stop_mngr]
            
            phones = ', '.join(users)
            Bot_tools.call_to(sender, log, pas, phones)
            
            #cursor = conn.cursor()
            #cursor.execute("SELECT id FROM mngrs;")
            #users = cursor.fetchall()
            #users = [str(i[0]) for i in users if str(i[0]) not in self.stop_mngr]
            
            #ids = ':'.join(users)
            #a = Bot_tools.send_app(ids)
            
            self.mngr_ords[id_ord] = {}
            self.mngr_ords[id_ord]['id'], self.mngr_ords[id_ord]['mngr'], self.mngr_ords[id_ord]['time'] = id_ord, 'null', int(time.time())
            self.mngr_ords[id_ord]['time'] = int(time.time())
            
            id_time = str(int(time.time()))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('💵Взять заявку💵', callback_data='mngr_order|{0}|{1}'.format(id_ord, id_time)))
            
            self.send_users = self.send_all(conn, '🔴НОВАЯ ЗАЯВКА🔴\nID: #{}'.format(id_time), 'mngr', markup)  
        
    def send_mas(self, order_hash, conn):
        cursor = conn.cursor()

        cursor.execute("UPDATE orders SET adress=? WHERE id=? ;", (str(order_hash['address']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET problem=? WHERE id=? ;", (str(order_hash['problem']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET raw_price=? WHERE id=? ;", (str(order_hash['raw_price']), order_hash['id_order'],))
        conn.commit()
        
        cursor.execute("SELECT tel FROM orders WHERE id=? ;", (order_hash['id_order'],))
        phone = cursor.fetchall()
        phone = phone[0][0]
        cursor.close()
        id_ord = order_hash['id_order']
        
        self.master_ords[id_ord] = {}
        self.master_ords[id_ord]['master'] = 'null'
        self.master_ords[id_ord]['id'] = id_ord
        self.master_ords[id_ord]['phone'] = phone
        self.master_ords[id_ord]['address'] = order_hash['address']
        self.master_ords[id_ord]['problem'] = order_hash['problem']
        self.master_ords[id_ord]['raw_price'] = order_hash['raw_price']
        
        id_time = str(int(time.time()))
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('💵Взять заявку💵', callback_data='master_order|{0}'.format(id_ord)))
        
        self.send_masters = self.send_all(conn, '🔴НОВАЯ ЗАЯВКА🔴\nID: #{}'.format(id_time), 'master', markup)         
    
    def new_client_full(self, order_hash, conn):
        pay_me, pay_ma = float(order_hash['price'])*0.05, float(order_hash['price'])*0.25
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET adress=? WHERE id=? ;", (str(order_hash['address']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET problem=? WHERE id=? ;", (str(order_hash['problem']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET raw_price=? WHERE id=? ;", (order_hash['raw_price'], order_hash['id_order'],))
        cursor.execute("UPDATE orders SET price=? WHERE id=? ;", (order_hash['price'], order_hash['id_order'],))
        cursor.execute("UPDATE orders SET master=? WHERE id=? ;", (str(order_hash['master']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET detail=? WHERE id=? ;", (str(order_hash['detail']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET detail_price=? WHERE id=? ;", (order_hash['detail_price'], order_hash['id_order'],))
        cursor.execute("UPDATE orders SET pay_ma=? WHERE id=? ;", (pay_ma, order_hash['id_order'],))
        cursor.execute("UPDATE orders SET pay_me=? WHERE id=? ;", (pay_me, order_hash['id_order'],))
        conn.commit()
        cursor.close()
    
    def master_accept(self, conn, call):
        bot = self.bot
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
            
        data_callback = call.data.split('|')
        id_ord = data_callback[1]
        if id_ord not in self.master_ords.keys():
            bot.send_message(call.message.chat.id, '❌Заявка не существует/была обработана❌')
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        elif self.master_ords[id_ord]['master'] != 'null':
            bot.send_message(call.message.chat.id, '❌Кто-то другой уже взял эту заявку❌')
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        else:
            if str(call.from_user.id) in self.send_masters.keys():
                del self.send_masters[str(call.from_user.id)]
            for id, mes in self.send_masters.items():
                bot.edit_message_reply_markup(id, mes, reply_markup=None)
                bot.delete_message(id, mes)
                
            if str(call.from_user.id) in self.stop_master:
                pass
            else:
                self.stop_master.append(str(call.from_user.id))
                 
            self.master_ords[id_ord]['master'] = self.in_state(call, conn, True)[0][0][5]     
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET master=? WHERE id=? ;", (str(self.master_ords[id_ord]['master']), id_ord,))
            conn.commit()
            cursor.close()
            
            bot.send_message(call.message.chat.id, self.master_ords[id_ord]['phone'])
            mrkp = types.InlineKeyboardMarkup()
            menu = types.InlineKeyboardButton('заполнить форму', callback_data='mas_q|'+id_ord)
            mrkp.add(menu)
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
            bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=mrkp)    
    
    def finish_format(self, order_hash, conn):
        pay_me, pay_ma = float(order_hash['price'])*0.05, float(order_hash['price'])*0.25
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET price=? WHERE id=? ;", (order_hash['price'], order_hash['id_order'],))
        cursor.execute("UPDATE orders SET detail=? WHERE id=? ;", (str(order_hash['detail']), order_hash['id_order'],))
        cursor.execute("UPDATE orders SET detail_price=? WHERE id=? ;", (order_hash['detail_price'], order_hash['id_order'],))
        cursor.execute("UPDATE orders SET pay_ma=? WHERE id=? ;", (pay_ma, order_hash['id_order'],))
        cursor.execute("UPDATE orders SET pay_me=? WHERE id=? ;", (pay_me, order_hash['id_order'],))
        conn.commit()
        cursor.close()        
        
    
    def all_orders(self, conn, chat):
        bot = self.bot
        cursor = conn.cursor()
        
        dt = datetime.datetime.now()
        dt = dt.microsecond
    
        workbook = xlsxwriter.Workbook('reps//{}.xlsx'.format(str(dt)))
        worksheet = workbook.add_worksheet()   
    
        cursor.execute("SELECT * FROM orders;")  
        data = cursor.fetchall()
        cursor.close()
        
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 7, 13)
        worksheet.set_column(1, 10, 15)
        worksheet.set_column(1, 11, 15)
        worksheet.set_column(1, 13, 15)
        worksheet.set_column(1, 14, 15)
        col = 0
        row = 0
        names = ('id','тел.','год','мес.','день','время','адрес','проблема','манагер','мастер','мастер зп','манагер зп','итог','озвуч. цена','дет.','цена дет.')
        for j in names:
            worksheet.write_string(row, col, j)
            col += 1
        
        clr = workbook.add_format({'bold':True, 'font_color':'red'})
        col2 = 0
        row2 = 1
        for i in data:
            if i[11] != None:
                clr = workbook.add_format({'bold':True, 'font_color':'green'})
            elif (i[8] != None) or (i[9] != None):
                clr = workbook.add_format({'bold':True, 'font_color':'blue'})
            for j in i:
                if j == None:
                    j = '-' 
                worksheet.write_string(row2,col2, str(j), clr)
                col2 += 1
            row2 += 1
            col2 = 0
        
        workbook.close()
        
        file = 'reps//{}.xlsx'.format(dt)
        doc = open(file,"rb")
        del data
        return bot.send_document(chat, doc)