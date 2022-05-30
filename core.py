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
from auth_token import key
from main import *

token = TOKEN
log = LOG
pas = PAS
sender = SENDER
super_users=['703799335','811147217']

# подключаем бд
conn = sqlite3.connect("db//galaktika.db", check_same_thread=False)
       
gb = help_bot(token)
gb.create_db(conn, key)
gb.bot.get_updates(allowed_updates=["channel_post","callback_query", "message"])

@gb.bot.message_handler(commands=['reset_key'])
def ref_key(msg):
    if str(msg.from_user.id) in super_users:
        a = Bot_tools.create_auth_token()
        gb.bot.send_message(msg.chat.id, 'Новый ключ регистрации:')
        gb.bot.send_message(msg.chat.id, '{}'.format(a))
        key = a
    else:
        gb.bot.send_message(msg.chat.id, '🔒Вам пока не доступна эта функция🔒')

@gb.bot.message_handler(commands=['view_key'])
def view_key(msg):
    if str(msg.from_user.id) in super_users:
        gb.bot.send_message(msg.chat.id, 'Ключ регистрации:{}'.format(key))        
    else:
        gb.bot.send_message(msg.chat.id, '🔒Вам пока не доступна эта функция🔒')
    
@gb.bot.message_handler(commands=['info'])
def info_bot(msg):
    if str(msg.from_user.id) in super_users:
        v_all = '/all_empls - показать всех сотрудников'
        v_one = '/find_empl - найти сотрудника'
        deleter = '/del_empl - уволить сотрудника'
        regi = '/register - зарегистрироваться'
        ords = '/ords - получить отчёт по заявкам'
        resetk = '/reset_key - поменять ключ регистрации'
        my_key = '/view_key - показать текущий ключ регистрации'
        menu = '{0}\n{1}\n{2}\n{3}\n{4}\n{5}'.format(v_all, v_one, deleter, regi, ords, resetk, my_key)
        gb.bot.send_message(msg.chat.id, menu)

# all orders
@gb.bot.message_handler(commands=['ords'])
def order_all(msg):
    if str(msg.from_user.id) in super_users:
        gb.all_orders(conn, msg.chat.id)
    else:
        gb.bot.send_message(msg.chat.id, '🔒Вам пока не доступна эта функция🔒')

# order with sart date and end date
@gb.bot.message_handler(commands=['ord_wh'])
def order_btwn(msg):
    if str(msg.from_user.id) in super_users:
        pass

# команда для удаления сотрудника
@gb.bot.message_handler(commands=['del_empl'])
def del_empl(msg):
    if str(msg.from_user.id) in super_users:
        mes = gb.bot.send_message(msg.chat.id, 'Введите имя сотрудника и должность (man/mas) как в примере: АндрейИванов-mas')
        gb.bot.register_next_step_handler(mes,go_del)
    else: 
        gb.bot.send_message(msg.chat.id, '🔒Вам пока не доступна эта функция🔒')

def go_del(msg):
    mes = msg.text.split('-')
    if len(mes) == 2:
        if gb.delete_emp(conn, mes[0], mes[1]) == 'succ':
            gb.bot.send_message(msg.chat.id, '✅Сотрудник успешно удалён✅')
        else:
            gb.bot.send_message(msg.chat.id, '❌Что-то пошло не так❌')

# команда для просмотра всех сотрудников
@gb.bot.message_handler(commands=['all_empls'])
def view_all(msg):
    if str(msg.from_user.id) in super_users:
        gb.view_empls(conn, msg.chat.id)
    else: 
        gb.bot.send_message(msg.chat.id, '🔒Вам пока не доступна эта функция🔒')

# команда для просмотра конкретного сотрудника
@gb.bot.message_handler(commands=['/find_empl'])
def finder(msg):
    if str(msg.from_user.id) in super_users:
        mes = gb.bot.send_message(msg.chat.id, 'Введите слитно имя и фамилию сотрудника')
        gb.bot.register_next_step_handler(mes, find_empl)
    else: 
        gb.bot.send_message(msg.chat.id, '🔒Вам пока не доступна эта функция🔒')

def find_empl(msg):
    name = msg.text
    employee = gb.view_empls(conn, msg.chat.id, name)
    gb.bot.send_message(msg.chat.id, str(employee))


''' start '''
@gb.bot.message_handler(commands=['start'])
def start(msg):
    if gb.in_state(msg, conn) == True:
        # возвращаются функции кабинета
        gb.bot.send_message(msg.chat.id, '✅Вы уже зарегистрированы✅')
    else:
        gb.bot.send_message(msg.chat.id, 'Вы не не подключены\n/register - зарегистрироваться\n/start - вернуться в начало')

# команда для регистрации
@gb.bot.message_handler(commands=['register'])
def start_reg(msg):
    # проверка юзера на нахождение d БД
    if gb.in_state(msg, conn) == True:
        # возвращаются функции кабинета
        pass    
    else:
        mes = gb.bot.send_message(msg.chat.id, 'Введите ключ доступа')
        gb.bot.register_next_step_handler(mes, auth)

def auth(msg):
    # аутентификация юзеров по общему токену
    user = 'n'+str(msg.from_user.id)
    if user in gb.pat:
        mes = gb.bot.send_message(msg.chat.id, 'Введите телефон')
        gb.bot.register_next_step_handler(mes, phone_form)        
  
    else: 
        state = gb.auth_check(msg.text, key, chat=msg.chat.id)
        if state == True:
            mes = gb.bot.send_message(msg.chat.id, 'Введите телефон')
            gb.bot.register_next_step_handler(mes, phone_form)       
        
def phone_form(msg):
    # парсинг телефона
    user = 'n'+str(msg.from_user.id)
    gb.pat[user] = {}
    gb.pat[user]['id'] = str(msg.from_user.id)
    tel = Bot_tools.tel_parser(msg.text)
    if tel == 'Incorrect / Not found':
        mes = gb.bot.send_message(msg.chat.id, '❌Не верный формат❌')
        return auth(msg)
    else:
        gb.pat[user]['phone'] = tel[0]
        mes = gb.bot.send_message(msg.chat.id, 'Введите имя и фамилию слитно')
        gb.bot.register_next_step_handler(mes, name_form)
        
def name_form(msg):
    # формирование заголовка и запрос имени
    user = 'n'+str(msg.from_user.id)
    gb.pat[user]['name'] = msg.text
    gb.pat[user]['chat'] = str(msg.chat.id) 
    date_obj = datetime.datetime.now()
    gb.pat[user]['year'], gb.pat[user]['month'], gb.pat[user]['day'] = date_obj.year, date_obj.month, date_obj.day
    del date_obj
    
    # переходим к выбору должности
    markup = types.InlineKeyboardMarkup()
    mE = types.InlineKeyboardButton('☎️Менеджер☎️', callback_data='mngr')
    mA = types.InlineKeyboardButton('🔧Мастер🔧', callback_data='mstr')
    markup.add(mA,mE)
    gb.bot.send_message(msg.chat.id, 'Выберите должность', reply_markup=markup)
    
# обработка входящих заказов 
@gb.bot.channel_post_handler()
def order_alert(msg):
    if msg.text[0] == '🔔':
        gb.alarm(msg, conn, sender, log, pas)

master_hash ={}
order_hash = {}
@gb.bot.callback_query_handler(func=lambda call : True)
def button_act(call):
    global order_hash
    if 'mngr_order' in call.data:
        data= call
        gb.order_accept(conn, data)
    
    if 'quiz' in call.data:
        id_ord = call.data.split('|')[1]
        order_hash[str(call.from_user.id)] = {}
        order_hash[str(call.from_user.id)]['id_order'] = id_ord
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
        mrkp = types.InlineKeyboardMarkup()
        menu = types.InlineKeyboardButton('✅Закрыт✅', callback_data='valid_client'+'|'+id_ord)
        menu2 = types.InlineKeyboardButton('❌Не закрыт❌', callback_data='not_vcl')
        mrkp.add(menu, menu2)
        gb.bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        gb.bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=mrkp)        
    
    if 'not_vcl' in call.data:      
        gb.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        del gb.stop_mngr[gb.stop_mngr.index(str(call.message.chat.id))]
    
    if 'valid_client' in call.data:
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id     
        new_id = call.data.replace('|','').replace('valid_client','')
        mes = gb.bot.send_message(call.message.chat.id, 'Ниже новый id этой заявки, введите его для продолжения оформления.')
        gb.bot.send_message(call.message.chat.id, new_id)
        gb.bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        gb.bot.register_next_step_handler(mes, id_order_new)
        
    if 'finish_order' in call.data:
        pass
    
    if 'mas_q' in call.data:
        id_ord = call.data.split('|')[1]
        master_hash[str(call.from_user.id)] = {}
        master_hash[str(call.from_user.id)]['id_order'] = id_ord
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id  
        ad = gb.master_ords[id_ord]['address']
        ph = gb.master_ords[id_ord]['phone']
        rp = gb.master_ords[id_ord]['raw_price']
        p = gb.master_ords[id_ord]['problem']
        
        inform = '🏠Адрес: {0}\n📱Телефон: {1}\n⚙️Проблема: {2}\n💰Цена: {3}'.format(ad, ph, p, rp)
        gb.bot.send_message(call.message.chat.id, inform)
        
        mes = gb.bot.send_message(call.message.chat.id, "Введите название детали")
        gb.bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        gb.bot.register_next_step_handler(mes, dtl)
        
    if 'master_order' in call.data:
        data = call
        gb.master_accept(conn, data)
    
    if call.data == 'mngr':
        data = call
        gb.mngr_reg(data, conn)
        
    if call.data == 'mstr':
        gb.master_reg(call, conn)
    
    if call.data == 'go_master':
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
        gb.bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)
        gb.bot.send_message(call.message.chat.id, '✅Вы успешно зкрыли заявку✅', reply_markup=types.ReplyKeyboardRemove())
        del gb.stop_mngr[gb.stop_mngr.index(str(call.message.chat.id))]
        gb.send_mas(order_hash[str(call.from_user.id)], conn)
        del gb.mngr_ords[order_hash[str(call.from_user.id)]['id_order']]
        del order_hash[str(call.from_user.id)]
        
    if call.data == 'next':
        __chat__ = call.message.chat.id
        __message__ = call.message.message_id
        gb.bot.edit_message_reply_markup(chat_id=__chat__, message_id=__message__, reply_markup=None)        
        mes = gb.bot.send_message(call.message.chat.id, 'Введите имя мастера', reply_markup=types.ReplyKeyboardRemove())
        gb.bot.register_next_step_handler(mes, mastr)        

msgs_del = []

@gb.bot.message_handler(commands=['42hf9sadjlsdjmf'])
def id_order_new(msg): 
    global order_hash
    if str(type(msg)) == "<class 'str'>":
        if 'bh' in msg:
            id_usr = msg.replace('bh|','')
            mes = gb.bot.send_message(id_usr, 'Введите озвученый прайс')
            gb.bot.register_next_step_handler(mes, raw_price)
            msgs_del.append([msg.chat.id, msg.message_id])
    else:    
        address = str(msg.text)
        if str(msg.text) in gb.mngr_ords.keys():
            mes = gb.bot.send_message(msg.chat.id, 'Введите озвученый прайс')
            gb.bot.register_next_step_handler(mes, raw_price)
            msgs_del.append([msg.chat.id, msg.message_id])
        else:
            mes = gb.bot.send_message(msg.chat.id, '❌заявка не найдена❌')
            msgs_del.append([msg.chat.id, msg.message_id])
            gb.bot.register_next_step_handler(mes, id_order_new)
            
def raw_price(msg):
    global order_hash
    if str(type(msg)) == "<class 'str'>":    
        if 'bh' in msg:
            id_usr = msg.replace('bh|','')
            mes = gb.bot.send_message(id_usr, 'Введите адрес')
            gb.bot.register_next_step_handler(mes, address)
            msgs_del.append([msg.chat.id, msg.message_id])
    else:
        try:
            rwp = int(str(msg.text))
            order_hash[str(msg.from_user.id)]['raw_price'] = rwp
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            bhnd = types.KeyboardButton(text='назад')
            markup.add(bhnd)
            mes = gb.bot.send_message(msg.chat.id, 'Введите адрес', reply_markup=markup)
            msgs_del.append([msg.chat.id, msg.message_id])
            return gb.bot.register_next_step_handler(mes, address)
        except:
            gb.bot.send_message(msg.chat.id, 'Не верный формат')
            prm = 'bh|'+str(msg.chat.id)
            msgs_del.append([msg.chat.id, msg.message_id])
            return id_order_new(prm)

def address(msg):
    global order_hash
    if msg.text == 'назад':
        prm = 'bh|'+str(msg.chat.id)
        return id_order_new(prm)
    else:
        address = order_hash[str(msg.from_user.id)]['address'] = msg.text
        mes = gb.bot.send_message(msg.chat.id, 'Введите проблему')
        gb.bot.register_next_step_handler(mes, problem)
        msgs_del.append([msg.chat.id, msg.message_id])

def problem(msg):
    global order_hash
    if msg.text == 'назад':
        prm = 'bh|'+str(msg.chat.id)
        return raw_price(prm)
    else:
        address = order_hash[str(msg.from_user.id)]['problem'] = msg.text
        if str(msg.from_user.id) in super_users:
            mrkp = types.InlineKeyboardMarkup()
            menu = types.InlineKeyboardButton('📩Отправить мастеру📩', callback_data='go_master')
            menu2 = types.InlineKeyboardButton('✏️Продолжить✏️', callback_data='next')
            mrkp.add(menu, menu2)            
            gb.bot.send_message(msg.chat.id, 'Выберите действие', reply_markup=mrkp)
            msgs_del.append([msg.chat.id, msg.message_id])
        else:
            gb.bot.send_message(msg.chat.id, '✅Вы успешно зкрыли заявку✅', reply_markup=types.ReplyKeyboardRemove())
            gb.send_mas(order_hash[str(msg.from_user.id)], conn)
            del gb.stop_mngr[gb.stop_mngr.index(str(msg.chat.id))]
            del gb.mngr_ords[order_hash[str(msg.from_user.id)]['id_order']]
            del order_hash[str(msg.from_user.id)]
            msgs_del.append([msg.chat.id, msg.message_id])

def mastr(msg):
    global order_hash, master_hash
    if str(msg.from_user.id) in super_users:
        order_hash[str(msg.from_user.id)]['master'] = msg.text
    mes = gb.bot.send_message(msg.chat.id, 'Введите название детали')
    msgs_del.append([msg.chat.id, msg.message_id])
    return gb.bot.register_next_step_handler(mes, dtl)
    
def dtl(msg):
    global order_hash, master_hash
    if str(type(msg)) == "<class 'str'>":
        if 'bh' in msg:
            id_usr = msg.replace('bh|','')
            mes = gb.bot.send_message(id_usr, 'Введите цену детали')
            gb.bot.register_next_step_handler(mes, dtl_prc)  
            msgs_del.append([msg.chat.id, msg.message_id])
    else:
        if str(msg.from_user.id) in super_users:
            order_hash[str(msg.from_user.id)]['detail'] = msg.text
        else:
            master_hash[str(msg.from_user.id)]['detail'] = msg.text
        mes = gb.bot.send_message(msg.chat.id, 'Введите цену детали')
        msgs_del.append([msg.chat.id, msg.message_id])
        return gb.bot.register_next_step_handler(mes, dtl_prc)

def dtl_prc(msg):
    global order_hash, master_hash
    if str(type(msg)) == "<class 'str'>":
        if 'bh' in msg:
            id_usr = msg.replace('bh|','')
            mes = gb.bot.send_message(id_usr, 'Введите итоговою цену')
            msgs_del.append([msg.chat.id, msg.message_id])
            gb.bot.register_next_step_handler(mes, finish_price)
    else:
        try:
            rwp = int(msg.text)
            if str(msg.from_user.id) in super_users:
                order_hash[str(msg.from_user.id)]['detail_price'] = rwp
            else:
                master_hash[str(msg.from_user.id)]['detail_price'] = rwp
            mes = gb.bot.send_message(msg.chat.id, 'Введите итоговою цену')
            msgs_del.append([msg.chat.id, msg.message_id])
            return gb.bot.register_next_step_handler(mes, finish_price)
        except:
            gb.bot.send_message(msg.chat.id, 'Не верный формат')
            prm = 'bh|'+str(msg.chat.id)
            msgs_del.append([msg.chat.id, msg.message_id])
            return dtl(prm)            
        
def finish_price(msg):
    global order_hash, master_hash      
    try:
        rwp = int(str(msg.text))
        if str(msg.from_user.id) in super_users:
            order_hash[str(msg.from_user.id)]['price'] = rwp
            gb.bot.send_message(msg.chat.id, '✅Вы успешно зкрыли заявку✅')
            del gb.stop_mngr[gb.stop_mngr.index(str(msg.chat.id))]
            gb.new_client_full(order_hash[str(msg.from_user.id)], conn)
            del gb.mngr_ords[order_hash[str(msg.from_user.id)]['id_order']]
            del order_hash[str(msg.from_user.id)]
            msgs_del.append([msg.chat.id, msg.message_id])
            for i in msgs_del:
                gb.bot.delete_message(i[0], i[1])
        else:
            master_hash[str(msg.from_user.id)]['price'] = rwp
            gb.bot.send_message(msg.chat.id, '✅Вы успешно зкрыли заявку✅')
            del gb.stop_master[gb.stop_master.index(str(msg.chat.id))]
            gb.finish_format(master_hash[str(msg.from_user.id)],conn)
            del gb.master_ords[master_hash[str(msg.from_user.id)]['id_order']]
            del master_hash[str(msg.from_user.id)]
            msgs_del.append([msg.chat.id, msg.message_id])
            for i in msgs_del:
                gb.bot.delete_message(i[0], i[1])
    except:
        gb.bot.send_message(msg.chat.id, 'Не верный формат')
        prm = 'bh|'+str(msg.chat.id)
        msgs_del.append([msg.chat.id, msg.message_id])
        for i in msgs_del:
            gb.bot.delete_message(i[0], i[1])
        return dtl_prc(prm)
 
if __name__ == '__main__':
    while True:
        try:
            print('Start...')
            gb.bot.polling(none_stop=True)
        except Exception as ex_:
            print(ex_)
            time.sleep(5)
            continue