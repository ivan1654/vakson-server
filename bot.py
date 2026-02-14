import pyautogui
import telebot
import time
import threading
import os
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
CHAT_ID = '1277953361'  # Твой ID для уведомлений

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


# --- СИСТЕМНЫЕ ФУНКЦИИ ---

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


# --- ЛОГИКА ОХОТЫ ---

def hunt_thread():
    global is_hunting
    while True:
        if is_hunting and is_authorized:
            try:
                if points['icon_click']:
                    pyautogui.click(points['icon_click'][0], points['icon_click'][1])
                    time.sleep(1)

                # Свайп вверх (листаем контент)
                w, h = pyautogui.size()
                pyautogui.moveTo(w // 2, int(h * 0.8))
                pyautogui.dragTo(w // 2, int(h * 0.2), duration=0.3)
                time.sleep(stream_wait_time)
            except:
                pass
        time.sleep(0.1)


# --- ИНТЕРФЕЙС ПРОГРАММЫ ---

class VaksonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vakson Control V2")
        self.root.geometry("350x500")
        self.root.configure(bg='#0f0f12')

        # Проверка сессии
        saved_key = load_session()
        if saved_key:
            self.auto_login(saved_key)
        else:
            self.draw_login()

    def draw_login(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="🔑 ВХОД В СИСТЕМУ", fg="#ffcc00", bg="#0f0f12", font=("Impact", 18)).pack(pady=40)
        self.key_entry = tk.Entry(self.root, justify='center', font=("Consolas", 12), bg="#1e1e24", fg="white",
                                  insertbackground="white")
        self.key_entry.pack(pady=10, padx=40, fill='x')
        tk.Button(self.root, text="АВТОРИЗОВАТЬСЯ", command=self.manual_login, bg="#ffcc00", fg="black",
                  font=("Arial", 10, "bold"), cursor="hand2").pack(pady=20, ipady=5, padx=60, fill='x')

    def auto_login(self, key):
        tk.Label(self.root, text="Проверка лицензии...", fg="white", bg="#0f0f12").pack(pady=100)
        threading.Thread(target=lambda: self.process_auth(key, silent=True), daemon=True).start()

    def manual_login(self):
        key = self.key_entry.get().strip().upper()
        if key: self.process_auth(key, silent=False)

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
                if not silent: messagebox.showerror("Ошибка", "Неверный ключ или HWID")
                self.draw_login()
        except:
            if not silent: messagebox.showerror("Ошибка", "Нет связи с сервером")
            self.draw_login()

    def draw_main(self):
        for w in self.root.winfo_children(): w.destroy()

        tk.Label(self.root, text="✅ СИСТЕМА LIVE", fg="#00ff00", bg="#0f0f12", font=("Impact", 24)).pack(pady=20)

        self.work_label = tk.Label(self.root, text="СТАТУС: ПАУЗА", fg="white", bg="#0f0f12",
                                   font=("Arial", 12, "bold"))
        self.work_label.pack(pady=10)

        # Кнопки управления
        tk.Button(self.root, text="▶️ ЗАПУСТИТЬ ОХОТУ", command=self.press_start, bg="#28a745", fg="white",
                  font=("Arial", 11, "bold"), height=2).pack(pady=10, padx=50, fill='x')
        tk.Button(self.root, text="🛑 ОСТАНОВИТЬ", command=self.press_stop, bg="#dc3545", fg="white",
                  font=("Arial", 11, "bold"), height=2).pack(pady=10, padx=50, fill='x')

        tk.Button(self.root, text="⚙️ НАСТРОЙКА ЗОН", command=self.open_setup, bg="#17a2b8", fg="white").pack(pady=15,
                                                                                                              padx=70,
                                                                                                              fill='x')

        tk.Button(self.root, text="ВЫЙТИ / СМЕНИТЬ КЛЮЧ", command=self.logout, bg="#333", fg="white",
                  font=("Arial", 8)).pack(side='bottom', pady=20)

    def press_start(self):
        global is_hunting
        if not points['icon_click']:
            messagebox.showwarning("Внимание", "Сначала настройте зоны (кнопка Настройка)!")
            return
        is_hunting = True
        self.work_label.config(text="СТАТУС: ОХОТА...", fg="#00ff00")
        bot_tg.send_message(CHAT_ID, "🚀 Охота запущена из приложения")

    def press_stop(self):
        global is_hunting
        is_hunting = False
        self.work_label.config(text="СТАТУС: ПАУЗА", fg="white")
        bot_tg.send_message(CHAT_ID, "🛑 Охота остановлена из приложения")

    def open_setup(self):
        class FakeMsg:
            def __init__(self): self.chat = type('obj', (object,), {'id': CHAT_ID})

        threading.Thread(target=run_setup_logic, args=(FakeMsg(),), daemon=True).start()
        messagebox.showinfo("Настройка", "Инструкции отправлены в Telegram бота!")

    def logout(self):
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        os.execl(sys.executable, sys.executable, *sys.argv)


# --- TELEGRAM ЛОГИКА ---

def main_k():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('▶️ ПУСК', '🛑 СТОП')
    m.add('📸 Скриншот', '📊 Инфо')
    m.add('⚙️ Настроить зоны')
    return m


def run_setup_logic(message):
    bot_tg.send_message(message.chat.id, "🎯 **Калибровка.**\nНаведи мышь на СУНДУК и жди 5 секунд...")
    time.sleep(5)
    p = pyautogui.position()
    points['icon_click'] = [p.x, p.y]
    save_settings()
    bot_tg.send_message(message.chat.id, f"✅ Точка {p.x}, {p.y} сохранена! Можно жать ПУСК.")


@bot_tg.message_handler(commands=['start'])
def st(m):
    if not is_authorized:
        bot_tg.send_message(m.chat.id, "🔒 Авторизуйтесь в программе на ПК.")
    else:
        bot_tg.send_message(m.chat.id, "🤖 Vakson Hunter на связи!", reply_markup=main_k())


@bot_tg.message_handler(func=lambda m: True)
def msg_handler(m):
    global is_hunting
    if not is_authorized: return

    if m.text == '▶️ ПУСК':
        is_hunting = True
        bot_tg.send_message(m.chat.id, "🚀 Поехали!")
    elif m.text == '🛑 СТОП':
        is_hunting = False
        bot_tg.send_message(m.chat.id, "🛑 Стоп.")
    elif m.text == '⚙️ Настроить зоны':
        threading.Thread(target=run_setup_logic, args=(m,), daemon=True).start()
    elif m.text == '📸 Скриншот':
        scr = pyautogui.screenshot()
        scr.save("snap.png")
        with open("snap.png", "rb") as f:
            bot_tg.send_photo(m.chat.id, f)
    elif m.text == '📊 Инфо':
        s = "РАБОТАЕТ" if is_hunting else "ПАУЗА"
        bot_tg.send_message(m.chat.id, f"Статус: {s}\nHWID: {get_hwid()}")


# --- ЗАПУСК ---

if __name__ == "__main__":
    threading.Thread(target=hunt_thread, daemon=True).start()
    threading.Thread(target=lambda: bot_tg.infinity_polling(none_stop=True), daemon=True).start()

    root = tk.Tk()
    app = VaksonApp(root)
    root.mainloop()