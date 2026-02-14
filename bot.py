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
import tkinter as tk
from tkinter import messagebox
from telebot import types

# --- КОНФИГУРАЦИЯ ---
SERVER_URL = "https://vakson-server.onrender.com"
API_TOKEN = '8463606697:AAEDD-2_SE3Fz369yw8PpfqwYLJtmp8Z5_Q'
CHAT_ID = '1277953361'  # Твой личный ID для отчетов

bot_tg = telebot.TeleBot(API_TOKEN)

# Состояния
is_hunting = False
is_authorized = False
stream_wait_time = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')

# Координаты (подгрузятся из файла)
areas = {'icon_area': None, 'btn_area': None, 'timer_area': None}
points = {'icon_click': None}


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


load_settings()


# --- ТЕЛЕГРАМ КЛАВИАТУРЫ ---
def main_k():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add('▶️ ПУСК', '🛑 СТОП')
    m.add('📸 Скриншот', '📊 Инфо')
    m.add('⚙️ Настройка зон')
    return m


# --- ЛОГИКА АВТО-НАСТРОЙКИ ---
def start_setup(message):
    """Пошаговая настройка через Телеграм"""

    def step_1(m):
        bot_tg.send_message(m.chat.id, "1️⃣ Наведи мышку на СУНДУК и подожди 3 сек...")
        time.sleep(3)
        p = pyautogui.position()
        points['icon_click'] = [p.x, p.y]
        # Делаем маленькую область вокруг клика для поиска иконки
        areas['icon_area'] = [p.x - 20, p.y - 20, 40, 40]
        bot_tg.send_message(m.chat.id, f"✅ Точка клика и зона поиска сохранены: {p.x}, {p.y}")

        bot_tg.send_message(m.chat.id, "2️⃣ Теперь открой сундук. Наведи на ТАЙМЕР и подожди 3 сек...")
        time.sleep(3)
        p2 = pyautogui.position()
        areas['timer_area'] = [p2.x - 30, p2.y - 10, 60, 20]
        bot_tg.send_message(m.chat.id, "✅ Зона таймера сохранена!")

        save_settings()
        bot_tg.send_message(m.chat.id, "🚀 Настройка завершена! Можно жать ПУСК.", reply_markup=main_k())

    step_1(message)


# --- ГЛАВНЫЙ ЦИКЛ ОХОТЫ ---
def hunt_logic():
    global is_hunting
    while True:
        if is_hunting and is_authorized:
            try:
                # Если настроена точка клика - просто кликаем и проверяем
                if points['icon_click']:
                    pyautogui.click(points['icon_click'][0], points['icon_click'][1])
                    time.sleep(2)
                    # Тут можно добавить логику проверки цвета или шаблона

                # Свайп вниз (листаем стрим)
                w, h = pyautogui.size()
                pyautogui.moveTo(w // 2, int(h * 0.8))
                pyautogui.dragTo(w // 2, int(h * 0.2), duration=0.3)
                time.sleep(stream_wait_time)
            except:
                pass
        time.sleep(0.5)


# --- GUI ---
class HunterGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Vakson Hunter")
        self.root.geometry("300x400")
        self.root.configure(bg='#1a1a1a')

        self.label = tk.Label(root, text="ВВЕДИТЕ КЛЮЧ", fg="white", bg="#1a1a1a", font=("Arial", 12))
        self.label.pack(pady=20)

        self.entry = tk.Entry(root, justify='center')
        self.entry.pack(pady=10)

        self.btn = tk.Button(root, text="ВОЙТИ", command=self.check_auth, bg="#4CAF50", fg="white")
        self.btn.pack(pady=20)

    def check_auth(self):
        global is_authorized
        key = self.entry.get().strip().upper()
        try:
            r = requests.get(f"{SERVER_URL}/check_key", params={"key": key, "hwid": get_hwid()}, timeout=5)
            if r.status_code == 200:
                is_authorized = True
                messagebox.showinfo("Успех", "Авторизация пройдена!")
                self.label.config(text="СИСТЕМА АКТИВНА", fg="#4CAF50")
                self.btn.config(state="disabled")
            else:
                messagebox.showerror("Ошибка", "Неверный ключ")
        except:
            messagebox.showerror("Ошибка", "Сервер не отвечает")


# --- ОБРАБОТКА ТЕЛЕГРАМ ---
@bot_tg.message_handler(commands=['start'])
def welcome(m):
    if not is_authorized:
        bot_tg.send_message(m.chat.id, "🔒 **Доступ закрыт.**\nСначала введи ключ в программе на ПК.")
    else:
        bot_tg.send_message(m.chat.id, "👋 Привет! Я готов к работе.", reply_markup=main_k())


@bot_tg.message_handler(func=lambda m: True)
def commands(m):
    global is_hunting
    if not is_authorized:
        bot_tg.send_message(m.chat.id, "⚠️ Ожидаю авторизации в EXE...")
        return

    if m.text == '▶️ ПУСК':
        if not points['icon_click']:
            bot_tg.send_message(m.chat.id, "❌ Сначала нажми '⚙️ Настройка зон'")
        else:
            is_hunting = True
            bot_tg.send_message(m.chat.id, "🚀 Поехали!")
    elif m.text == '🛑 СТОП':
        is_hunting = False
        bot_tg.send_message(m.chat.id, "🛑 Остановлено.")
    elif m.text == '⚙️ Настройка зон':
        threading.Thread(target=start_setup, args=(m,)).start()
    elif m.text == '📊 Инфо':
        status = "✅ Работает" if is_hunting else "🛑 Пауза"
        bot_tg.send_message(m.chat.id, f"Статус: {status}\nКлюч активен: Да\nHWID: {get_hwid()}")


# --- ЗАПУСК ВСЕГО ---
if __name__ == "__main__":
    # 1. Поток для охоты
    threading.Thread(target=hunt_logic, daemon=True).start()

    # 2. Поток для Телеграм (ОДИН РАЗ!)
    threading.Thread(target=lambda: bot_tg.infinity_polling(none_stop=True), daemon=True).start()

    # 3. Главное окно (GUI)
    root = tk.Tk()
    app = HunterGui(root)
    root.mainloop()& "C:\Program Files\Git\bin\git.exe" status