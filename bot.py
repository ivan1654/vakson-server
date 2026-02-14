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

# --- КОНФИГУРАЦИЯ БЕЗОПАСНОСТИ ---
SERVER_URL = "https://vakson-server.onrender.com"
HEADERS = {"ngrok-skip-browser-warning": "true"}
API_TOKEN = '8463606697:AAEDD-2_SE3Fz369yw8PpfqwYLJtmp8Z5_Q'
CHAT_ID = '1277953361'

bot = telebot.TeleBot(API_TOKEN)
current_user_key = None
is_authorized = False
tg_access_granted = False

# --- ПАРАМЕТРЫ ОХОТЫ ---
pyautogui.PAUSE = 0.01
is_hunting = False
is_reporting = True
stream_wait_time = 5
ANIMATION_DELAY = 2.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_MAP = {
    'время': 'time_sample.png',
    'табло': 'tablo_view.png',
    'ок': 'ok_sample.png',
    'открыть': 'open_btn.png'
}
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
SESSION_FILE = os.path.join(BASE_DIR, 'session.json')

samples = {'icon': None}
areas = {'icon_area': None, 'btn_area': None, 'timer_area': None}
points = {'icon_click': None}


# --- СИСТЕМА ФАЙЛОВ И HWID ---

def get_hwid():
    try:
        cmd = 'wmic csproduct get uuid'
        return subprocess.check_output(cmd, shell=True).decode('utf-8').split('\n')[1].strip()
    except:
        return f"{socket.gethostname()}-{os.getlogin()}"


def save_settings():
    data = {'areas': areas, 'points': points, 'wait': stream_wait_time}
    with open(SETTINGS_FILE, 'w') as f: json.dump(data, f)


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
    with open(SESSION_FILE, 'w') as f: json.dump({'key': key}, f)


def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f).get('key')
        except:
            return None
    return None


load_settings()


# --- МЕНЮ ТЕЛЕГРАМ ---

def main_k():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('▶️ ПУСК', '🛑 СТОП')
    m.add('📸 Скриншот', '📊 Инфо')
    m.add('🛠 Взаимодействие', '⚙️ Настройки координат')
    return m


def interact_k():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('💾 Сохранить всё', '✏️ Ввод ВРУЧНУЮ')
    m.add('🗑 Удалить данные', '🏠 Назад')
    return m


def settings_k():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    m.add('📦 Координаты сундука', '🔘 Координаты табло')
    m.add('⏱ Координаты таймера', '📍 Точка клика')
    m.add('⏳ Время на стриме', '🏠 Назад')
    return m


# --- ЛОГИКА ОХОТЫ ---

def tapping_action():
    if not areas['timer_area']: return
    tx, ty, tw, th = areas['timer_area']
    for i in range(250):
        if not is_hunting: break
        pyautogui.click(tx + random.randint(5, tw - 5), ty + random.randint(5, th - 5))
        if i % 15 == 0 and not safe_locate('табло', areas['btn_area'], 0.4): break
        time.sleep(0.01)
    time.sleep(2.5)
    pyautogui.click(tx + tw // 2, ty + th // 2)


def safe_locate(img_name, region, conf=0.5):
    img_path = os.path.join(BASE_DIR, FILE_MAP.get(img_name, ''))
    if not os.path.exists(img_path) or region is None: return None
    try:
        return pyautogui.locateOnScreen(img_path, region=region, confidence=conf, grayscale=True)
    except:
        return None


def hunt_logic():
    global is_hunting
    while True:
        if is_hunting and is_authorized:
            try:
                # Поиск иконки сундука
                if areas['icon_area']:
                    # Если есть сохраненный скриншот иконки
                    res = None
                    if samples['icon']:
                        res = pyautogui.locateOnScreen(samples['icon'], region=areas['icon_area'], confidence=0.7)

                    if res or points['icon_click']:
                        # Кликаем (либо по найденному, либо по заданному)
                        click_pt = res if res else points['icon_click']
                        pyautogui.click(click_pt)
                        time.sleep(ANIMATION_DELAY)

                        # Проверяем открылось ли табло
                        if safe_locate('табло', areas['btn_area'], 0.4):
                            tapping_action()

                # Свайп
                w, h = pyautogui.size()
                pyautogui.moveTo(w // 2, int(h * 0.8))
                pyautogui.dragTo(w // 2, int(h * 0.2), duration=0.3)
                time.sleep(stream_wait_time)
            except:
                time.sleep(1)
        time.sleep(0.1)


# --- ИНТЕРФЕЙС ПК (TKINTER) ---

class VaksonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vakson Hunter PRO")
        self.root.geometry("350x450")
        self.root.configure(bg='#0f0f12')
        saved_key = load_session()
        if saved_key:
            self.auto_login(saved_key)
        else:
            self.draw_login()

    def draw_login(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="🔑 ВХОД", fg="#ffcc00", bg="#0f0f12", font=("Impact", 20)).pack(pady=40)
        self.key_entry = tk.Entry(self.root, justify='center', font=("Consolas", 12))
        self.key_entry.pack(pady=10, padx=40, fill='x')
        tk.Button(self.root, text="ВОЙТИ", command=self.manual_login, bg="#ffcc00").pack(pady=20, padx=80, fill='x')

    def manual_login(self):
        key = self.key_entry.get().strip().upper()
        if key: self.process_auth(key)

    def auto_login(self, key):
        threading.Thread(target=lambda: self.process_auth(key), daemon=True).start()

    def process_auth(self, key):
        global is_authorized, current_user_key
        try:
            r = requests.get(f"{SERVER_URL}/check_key", params={"key": key, "hwid": get_hwid()}, headers=HEADERS,
                             timeout=10)
            if r.status_code == 200:
                is_authorized = True
                current_user_key = key
                save_session(key)
                self.draw_main()
            else:
                self.draw_login()
        except:
            self.draw_login()

    def draw_main(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="✅ СИСТЕМА LIVE", fg="#00ff00", bg="#0f0f12", font=("Impact", 24)).pack(pady=30)
        self.work_label = tk.Label(self.root, text="СТАТУС: ПАУЗА", fg="white", bg="#0f0f12")
        self.work_label.pack(pady=10)
        tk.Button(self.root, text="▶️ ПУСК", command=self.start_h, bg="#28a745", fg="white",
                  font=("Arial", 12, "bold")).pack(pady=10, padx=60, fill='x')
        tk.Button(self.root, text="🛑 СТОП", command=self.stop_h, bg="#dc3545", fg="white",
                  font=("Arial", 12, "bold")).pack(pady=10, padx=60, fill='x')
        tk.Button(self.root, text="ВЫХОД", command=self.logout, bg="#333", fg="white").pack(side='bottom', pady=20)

    def start_h(self):
        global is_hunting;
        is_hunting = True
        self.work_label.config(text="СТАТУС: ОХОТА", fg="#00ff00")

    def stop_h(self):
        global is_hunting;
        is_hunting = False
        self.work_label.config(text="СТАТУС: ПАУЗА", fg="white")

    def logout(self):
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        os.execl(sys.executable, sys.executable, *sys.argv)


# --- ОБРАБОТЧИК ТЕЛЕГРАМ ---

@bot.message_handler(commands=['start'])
def st(m):
    global tg_access_granted
    tg_access_granted = False
    bot.send_message(m.chat.id, "🔐 Пришли свой КЛЮЧ для доступа к командам.")


@bot.message_handler(func=lambda m: True)
def h(m):
    global is_hunting, stream_wait_time, tg_access_granted

    # ПРОВЕРКА ДОСТУПА
    if not tg_access_granted:
        if is_authorized and m.text.strip().upper() == current_user_key:
            tg_access_granted = True
            bot.send_message(m.chat.id, "✅ Доступ разрешен!", reply_markup=main_k())
        else:
            bot.send_message(m.chat.id, "❌ Неверный ключ или бот на ПК не запущен.")
        return

    # ОСНОВНЫЕ КОМАНДЫ
    if m.text == '▶️ ПУСК':
        is_hunting = True; bot.send_message(m.chat.id, "🚀 Старт!")
    elif m.text == '🛑 СТОП':
        is_hunting = False; bot.send_message(m.chat.id, "🛑 Стоп.")
    elif m.text == '📸 Скриншот':
        p = os.path.join(BASE_DIR, 'live.png')
        pyautogui.screenshot(p)
        with open(p, 'rb') as f:
            bot.send_photo(m.chat.id, f)

    elif m.text == '📊 Инфо':
        msg = "📊 <b>СТАТУС:</b>\n"
        for k, v in FILE_MAP.items():
            status = "✅" if os.path.exists(os.path.join(BASE_DIR, v)) else "❌"
            msg += f"{status} {k.capitalize()}\n"
        msg += f"\n⏳ Ожидание: <b>{stream_wait_time}с</b>"
        bot.send_message(m.chat.id, msg, parse_mode="HTML")

    elif m.text == '🛠 Взаимодействие':
        bot.send_message(m.chat.id, "Меню:", reply_markup=interact_k())
    elif m.text == '⚙️ Настройки координат':
        bot.send_message(m.chat.id, "Зоны:", reply_markup=settings_k())
    elif m.text == '🏠 Назад':
        bot.send_message(m.chat.id, "Меню:", reply_markup=main_k())

    elif m.text == '💾 Сохранить всё':
        save_settings(); bot.send_message(m.chat.id, "💾 Сохранено!")

    # Ручная настройка координат (твои команды)
    elif m.text in ['📦 Координаты сундука', '🔘 Координаты табло', '⏱ Координаты таймера']:
        cmd = m.text
        bot.send_message(m.chat.id, "⬆️ Лево-Верх (5с)");
        time.sleep(5);
        p1 = pyautogui.position()
        bot.send_message(m.chat.id, "⬇️ Право-Низ (5с)");
        time.sleep(5);
        p2 = pyautogui.position()
        x, y, w, h = min(p1.x, p2.x), min(p1.y, p2.y), abs(p1.x - p2.x), abs(p1.y - p2.y)
        if 'сундука' in cmd:
            areas['icon_area'] = [x, y, w, h]
            samples['icon'] = pyautogui.screenshot(region=(x, y, w, h))
        elif 'табло' in cmd:
            areas['btn_area'] = [x, y, w, h]
        elif 'таймера' in cmd:
            areas['timer_area'] = [x, y, w, h]
        bot.send_message(m.chat.id, "✅ Зона настроена!")

    elif m.text == '📍 Точка клика':
        bot.send_message(m.chat.id, "📍 Наведи на сундук (5с)");
        time.sleep(5)
        points['icon_click'] = [pyautogui.position().x, pyautogui.position().y]
        bot.send_message(m.chat.id, "✅ Точка сохранена!")

    elif m.text == '⏳ Время на стриме':
        km = types.InlineKeyboardMarkup()
        btns = [types.InlineKeyboardButton(f"{t}с", callback_data=f"w_{t}") for t in [5, 10, 15, 30]]
        km.add(*btns);
        bot.send_message(m.chat.id, "Интервал:", reply_markup=km)


@bot.callback_query_handler(func=lambda call: call.data.startswith("w_"))
def callback_wait(call):
    global stream_wait_time
    stream_wait_time = int(call.data.split("_")[1])
    bot.edit_message_text(f"✅ Установлено: {stream_wait_time}с", call.message.chat.id, call.message.message_id)


if __name__ == "__main__":
    threading.Thread(target=hunt_logic, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True).start()
    root = tk.Tk()
    app = VaksonApp(root)
    root.mainloop()