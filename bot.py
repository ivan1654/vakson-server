import pyautogui
import telebot
import time
import threading
import os
import random
import json
import requests
import subprocess
import socket
import sys
import tkinter as tk
from tkinter import messagebox
from telebot import types

# --- КОНФИГУРАЦИЯ ---
SERVER_URL = "https://vakson-server.onrender.com"
HEADERS = {"ngrok-skip-browser-warning": "true"}
API_TOKEN = '8463606697:AAEDD-2_SE3Fz369yw8PpfqwYLJtmp8Z5_Q'
CHAT_ID = '1277953361'  # Твой ID для отчетов

bot_tg = telebot.TeleBot(API_TOKEN)
pyautogui.PAUSE = 0.01

# Состояния
is_hunting = False
is_authorized = False
stream_wait_time = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
SESSION_FILE = os.path.join(BASE_DIR, 'session.json')

# Координаты
areas = {'icon_area': None, 'btn_area': None, 'timer_area': None}
points = {'icon_click': None}


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_hwid():
    try:
        cmd = 'wmic csproduct get uuid'
        return subprocess.check_output(cmd, shell=True).decode('utf-8').split('\n')[1].strip()
    except:
        return f"{socket.gethostname()}-{os.getlogin()}"


def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump({'areas': areas, 'points': points, 'wait': stream_wait_time}, f)


def load_settings():
    global stream_wait_time
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                areas.update(data.get('areas', {}))
                points.update(data.get('points', {}))
                stream_wait_time = data.get('wait', 5)
        except:
            pass


def save_session(key):
    with open(SESSION_FILE, 'w') as f:
        json.dump({'key': key}, f)


def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f).get('key')
        except:
            return None
    return None


load_settings()


# --- ЛОГИКА АВТО-НАСТРОЙКИ ЧЕРЕЗ ТГ ---

def run_setup_logic(message):
    bot_tg.send_message(message.chat.id,
                        "🎯 **Начинаем настройку.**\nУ тебя есть 5 секунд, чтобы навести мышку на нужную точку.")

    # Шаг 1: Сундук
    time.sleep(5)
    p_icon = pyautogui.position()
    points['icon_click'] = [p_icon.x, p_icon.y]
    areas['icon_area'] = [p_icon.x - 25, p_icon.y - 25, 50, 50]
    bot_tg.send_message(message.chat.id, f"✅ Точка клика сохранена: {p_icon.x}, {p_icon.y}")

    # Шаг 2: Таймер
    bot_tg.send_message(message.chat.id, "⏱ Теперь наведи на ТАЙМЕР (внутри открытого сундука) и подожди 5 сек...")
    time.sleep(5)
    p_timer = pyautogui.position()
    areas['timer_area'] = [p_timer.x - 40, p_timer.y - 10, 80, 20]

    save_settings()
    bot_tg.send_message(message.chat.id, "🚀 **Настройка готова!** Можно запускать охоту.", reply_markup=main_k())


# --- ЦИКЛ ОХОТЫ ---

def hunt_thread():
    global is_hunting
    while True:
        if is_hunting and is_authorized:
            try:
                # Клик по сундуку, если есть координаты
                if points['icon_click']:
                    pyautogui.click(points['icon_click'][0], points['icon_click'][1])
                    time.sleep(1)

                # Свайп (прокрутка стримов)
                w, h = pyautogui.size()
                pyautogui.moveTo(w // 2, int(h * 0.8))
                pyautogui.dragTo(w // 2, int(h * 0.2), duration=0.3)
                time.sleep(stream_wait_time)
            except:
                pass
        time.sleep(0.1)


# --- ИНТЕРФЕЙС TKINTER ---

class VaksonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vakson Control")
        self.root.geometry("320x450")
        self.root.configure(bg='#0f0f12')

        saved_key = load_session()
        if saved_key:
            self.auto_login(saved_key)
        else:
            self.draw_login()

    def draw_login(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="🔑 АВТОРИЗАЦИЯ", fg="#ffcc00", bg="#0f0f12", font=("Impact", 18)).pack(pady=30)
        self.key_entry = tk.Entry(self.root, justify='center', font=("Consolas", 12))
        self.key_entry.pack(pady=10, padx=30, fill='x')
        tk.Button(self.root, text="ПОДТВЕРДИТЬ", command=self.manual_login, bg="#ffcc00",
                  font=("Arial", 10, "bold")).pack(pady=20, ipady=5, padx=50, fill='x')

    def auto_login(self, key):
        threading.Thread(target=lambda: self.process_auth(key, silent=True), daemon=True).start()

    def manual_login(self):
        key = self.key_entry.get().strip().upper()
        if not key: return
        self.process_auth(key, silent=False)

    def process_auth(self, key, silent=False):
        global is_authorized
        try:
            r = requests.get(f"{SERVER_URL}/check_key", params={"key": key, "hwid": get_hwid()}, headers=HEADERS,
                             timeout=10)
            if r.status_code == 200:
                is_authorized = True
                save_session(key)
                self.draw_main()
            else:
                if not silent:
                    messagebox.showerror("Ошибка", "Ключ неверен или HWID занят")
                else:
                    self.draw_login()
        except:
            if not silent: messagebox.showerror("Ошибка", "Сервер спит или недоступен")

    def draw_main(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="✅ СИСТЕМА LIVE", fg="#00ff00", bg="#0f0f12", font=("Impact", 20)).pack(pady=40)
        tk.Button(self.root, text="ВЫЙТИ / СМЕНИТЬ КЛЮЧ", command=self.logout, bg="#333", fg="white").pack(
            side='bottom', pady=20)

    def logout(self):
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        os.execl(sys.executable, sys.executable, *sys.argv)


# --- TELEGRAM HANDLERS ---

def main_k():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('▶️ ПУСК', '🛑 СТОП')
    m.add('📸 Скриншот', '📊 Инфо')
    m.add('⚙️ Настроить зоны')
    return m


@bot_tg.message_handler(commands=['start'])
def st(m):
    if not is_authorized:
        bot_tg.send_message(m.chat.id, "🔒 **Доступ ограничен.**\nВведите ключ в приложении на ПК для активации.")
    else:
        bot_tg.send_message(m.chat.id, "🤖 Vakson Hunter готов!", reply_markup=main_k())


@bot_tg.message_handler(func=lambda m: True)
def msg_handler(m):
    global is_hunting
    if not is_authorized:
        bot_tg.send_message(m.chat.id, "⚠️ Ожидаю авторизации в EXE...")
        return

    if m.text == '▶️ ПУСК':
        if not points['icon_click']:
            bot_tg.send_message(m.chat.id, "❌ Сначала нажми '⚙️ Настроить зоны'")
        else:
            is_hunting = True
            bot_tg.send_message(m.chat.id, "🚀 Охота началась!")
    elif m.text == '🛑 СТОП':
        is_hunting = False
        bot_tg.send_message(m.chat.id, "🛑 Пауза.")
    elif m.text == '⚙️ Настроить зоны':
        threading.Thread(target=run_setup_logic, args=(m,), daemon=True).start()
    elif m.text == '📊 Инфо':
        status = "РАБОТАЕТ" if is_hunting else "ПАУЗА"
        bot_tg.send_message(m.chat.id, f"📊 Статус: {status}\n📍 Точка: {points['icon_click']}")


# --- ЗАПУСК ---

if __name__ == "__main__":
    # Запуск логики охоты
    threading.Thread(target=hunt_thread, daemon=True).start()

    # Запуск Telegram (Один раз, none_stop чтобы не вылетал)
    threading.Thread(target=lambda: bot_tg.infinity_polling(none_stop=True), daemon=True).start()

    # Запуск GUI
    root = tk.Tk()
    app = VaksonApp(root)
    root.mainloop()