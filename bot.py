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
from PIL import Image, ImageTk
from io import BytesIO

# --- КОНФИГУРАЦИЯ ---
# ТВОЯ АКТУАЛЬНАЯ ССЫЛКА НА RENDER
SERVER_URL = "https://vakson-server.onrender.com"
HEADERS = {"ngrok-skip-browser-warning": "true"}
API_TOKEN = '8463606697:AAEDD-2_SE3Fz369yw8PpfqwYLJtmp8Z5_Q'
CHAT_ID = '1277953361'

bot_tg = telebot.TeleBot(API_TOKEN)
pyautogui.PAUSE = 0.01

# Состояния
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

samples = {'icon': None}
areas = {'icon_area': None, 'btn_area': None, 'timer_area': None}
points = {'icon_click': None}

# --- СИСТЕМА ФАЙЛОВ И НАСТРОЕК ---

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
                if areas['icon_area']:
                    samples['icon'] = pyautogui.screenshot(region=areas['icon_area'])
        except: pass

load_settings()

# --- КЛАВИАТУРЫ ТЕЛЕГРАМ ---

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

def send_report(text, with_photo=False):
    if is_reporting:
        try:
            if with_photo:
                p = os.path.join(BASE_DIR, 'live.png')
                pyautogui.screenshot(p)
                with open(p, 'rb') as f:
                    bot_tg.send_photo(CHAT_ID, f, caption=f"📢 {text}")
            else:
                bot_tg.send_message(CHAT_ID, f"📢 {text}")
        except: pass

def safe_locate(img_name, region, conf=0.5):
    img_path = os.path.join(BASE_DIR, FILE_MAP.get(img_name, ''))
    if not os.path.exists(img_path) or region is None: return None
    try:
        return pyautogui.locateOnScreen(img_path, region=region, confidence=conf, grayscale=True)
    except: return None

def tapping_action():
    if not areas['timer_area']: return
    tx, ty, tw, th = areas['timer_area']
    for i in range(250):
        if not is_hunting: break
        pyautogui.click(tx + random.randint(5, tw - 5), ty + random.randint(5, th - 5))
        if i % 15 == 0 and not safe_locate('табло', areas['btn_area'], 0.4): break
        time.sleep(0.01)
    time.sleep(2.5)
    send_report("✅ Выполнено!", with_photo=True)
    if areas['timer_area']:
        pyautogui.click(tx + tw // 2, ty + th // 2)

def hunt_logic_thread():
    global is_hunting
    while True:
        if is_hunting:
            try:
                if samples['icon'] and areas['icon_area']:
                    res = pyautogui.locateOnScreen(samples['icon'], region=areas['icon_area'], confidence=0.7, grayscale=True)
                    if res:
                        send_report("Сундук найден!")
                        opened = False
                        for _ in range(2):
                            if points['icon_click']:
                                pyautogui.click(points['icon_click'])
                                time.sleep(ANIMATION_DELAY)
                                if safe_locate('табло', areas['btn_area'], 0.4): opened = True; break
                        if opened:
                            if safe_locate('открыть', areas['timer_area'], 0.7):
                                send_report("⚡ Мгновенный сундук!", with_photo=True)
                                tapping_action()
                            else:
                                tapping = False
                                limit = time.time() + 310
                                while time.time() < limit and is_hunting:
                                    if safe_locate('время', areas['timer_area'], 0.9): tapping = True; break
                                    if not safe_locate('табло', areas['btn_area'], 0.4): break
                                    time.sleep(0.05)
                                if tapping:
                                    send_report("🔥 ВРЕМЯ ПОШЛО!", with_photo=True)
                                    tapping_action()

                if is_hunting:
                    w, h = pyautogui.size()
                    pyautogui.moveTo(w // 2, int(h * 0.8))
                    pyautogui.dragTo(w // 2, int(h * 0.2), duration=0.3, button='left')
                    time.sleep(stream_wait_time)
            except: time.sleep(1)
        time.sleep(0.1)

# --- GUI ИНТЕРФЕЙС ---

class HunterGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Vakson Loader")
        self.root.geometry("360x520")
        self.root.configure(bg='#0d0d12')
        self.show_auth()

    def show_auth(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="🛡️", font=("Arial", 50), bg='#0d0d12', fg='#ffcc00').pack(pady=20)
        tk.Label(self.root, text="ВХОД В СИСТЕМУ", font=("Impact", 18), bg='#0d0d12', fg='white').pack()
        self.key_ent = tk.Entry(self.root, justify='center', font=("Consolas", 14), bg='#16161d', fg='white', borderwidth=0)
        self.key_ent.pack(pady=30, ipady=8, padx=40, fill='x')
        tk.Button(self.root, text="АВТОРИЗАЦИЯ", command=self.auth, bg='#ffcc00', font=("Arial", 10, "bold")).pack(ipady=10, padx=40, fill='x')

    def auth(self):
        key = self.key_ent.get().strip().upper()
        try:
            # Запрос к твоему новому серверу
            r = requests.get(f"{SERVER_URL}/check_key", params={"key": key, "hwid": get_hwid()}, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                self.show_main()
                threading.Thread(target=lambda: bot_tg.infinity_polling(), daemon=True).start()
                threading.Thread(target=hunt_logic_thread, daemon=True).start()
            else: messagebox.showerror("Ошибка", "Ключ неверен или HWID не совпадает")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Нет связи с сервером Render!\nПроверь статус в панели Render.")

    def show_main(self):
        for w in self.root.winfo_children(): w.destroy()
        try:
            conf = requests.get(f"{SERVER_URL}/get_config", headers=HEADERS).json()
            self.root.title(conf.get('title', 'HUNTER'))
        except: pass

        tk.Label(self.root, text="ПАНЕЛЬ УПРАВЛЕНИЯ", font=("Impact", 20), bg='#0d0d12', fg='#ffcc00').pack(pady=20)
        self.stat_btn = tk.Button(self.root, text="СТАТУС: ПАУЗА", bg='#16161d', fg='white', font=("Arial", 12, "bold"), state='disabled')
        self.stat_btn.pack(pady=10, padx=40, fill='x', ipady=15)

        tk.Button(self.root, text="ЗАПУСТИТЬ", command=self.on, bg='#28a745', fg='white', font=("Arial", 11, "bold")).pack(pady=5, ipady=10, padx=40, fill='x')
        tk.Button(self.root, text="ОСТАНОВИТЬ", command=self.off, bg='#c82333', fg='white', font=("Arial", 11, "bold")).pack(pady=5, ipady=10, padx=40, fill='x')
        tk.Label(self.root, text="Управление также доступно в Telegram", bg='#0d0d12', fg='#444', font=("Arial", 8)).pack(side='bottom', pady=10)

    def on(self):
        global is_hunting; is_hunting = True; self.stat_btn.config(text="СТАТУС: РАБОТАЕТ", bg='#28a745')

    def off(self):
        global is_hunting; is_hunting = False; self.stat_btn.config(text="СТАТУС: ПАУЗА", bg='#16161d')

# --- ТЕЛЕГРАМ ОБРАБОТЧИКИ (ОСТАВЛЕНО БЕЗ ИЗМЕНЕНИЙ) ---

@bot_tg.message_handler(commands=['start'])
def st(m):
    bot_tg.send_message(m.chat.id, "🤖 <b>Бот-охотник Vakson Edition</b>", parse_mode="HTML", reply_markup=main_k())

@bot_tg.message_handler(func=lambda m: True)
def h(m):
    global is_hunting, stream_wait_time
    if m.text == '▶️ ПУСК':
        is_hunting = True; bot_tg.send_message(m.chat.id, "🚀 Старт!")
    elif m.text == '🛑 СТОП':
        is_hunting = False; bot_tg.send_message(m.chat.id, "🛑 Стоп.")
    elif m.text == '📸 Скриншот':
        send_report("Текущий экран:", with_photo=True)
    elif m.text == '📊 Инфо':
        msg = "📊 <b>СТАТУС:</b>\n"
        for k, v in FILE_MAP.items():
            status = "✅" if os.path.exists(os.path.join(BASE_DIR, v)) else "❌"
            msg += f"{status} {k.capitalize()}\n"
        msg += f"\n📐 <b>КООРДИНАТЫ ЗОН:</b>\n"
        msg += f"• Сундук: <code>{areas['icon_area']}</code>\n"
        msg += f"• Табло: <code>{areas['btn_area']}</code>\n"
        msg += f"• Таймер: <code>{areas['timer_area']}</code>\n"
        msg += f"• Клик: <code>{points['icon_click']}</code>\n\n"
        msg += f"⏳ Ожидание: <b>{stream_wait_time}с</b>"
        bot_tg.send_message(m.chat.id, msg, parse_mode="HTML")
    elif m.text == '🛠 Взаимодействие':
        bot_tg.send_message(m.chat.id, "Меню:", reply_markup=interact_k())
    elif m.text == '⚙️ Настройки координат':
        bot_tg.send_message(m.chat.id, "Зоны:", reply_markup=settings_k())
    elif m.text == '🏠 Назад':
        bot_tg.send_message(m.chat.id, "Меню:", reply_markup=main_k())
    elif m.text == '💾 Сохранить всё':
        save_settings(); bot_tg.send_message(m.chat.id, "💾 Сохранено!")
    elif m.text == '🗑 Удалить данные':
        for a in areas: areas[a] = None
        if os.path.exists(SETTINGS_FILE): os.remove(SETTINGS_FILE)
        bot_tg.send_message(m.chat.id, "🗑 Очищено!")
    elif m.text == '✏️ Ввод ВРУЧНУЮ':
        bot_tg.send_message(m.chat.id, "Формат: <code>таймер x y w h</code>", parse_mode="HTML")
    elif m.text.startswith(('таймер ', 'табло ', 'сундук ')):
        try:
            p = m.text.split(); coords = [int(p[1]), int(p[2]), int(p[3]), int(p[4])]
            if 'таймер' in p[0]: areas['timer_area'] = coords
            elif 'табло' in p[0]: areas['btn_area'] = coords
            elif 'сундук' in p[0]: areas['icon_area'] = coords
            bot_tg.send_message(m.chat.id, f"✅ Зона {p[0]} сохранена!")
        except: bot_tg.send_message(m.chat.id, "❌ Ошибка формата!")
    elif m.text.startswith('клик '):
        try:
            p = m.text.split(); points['icon_click'] = [int(p[1]), int(p[2])]
            bot_tg.send_message(m.chat.id, "✅ Точка клика сохранена!")
        except: bot_tg.send_message(m.chat.id, "❌ Ошибка!")
    elif m.text in ['📦 Координаты сундука', '🔘 Координаты табло', '⏱ Координаты таймера']:
        bot_tg.send_message(m.chat.id, "⬆️ Левый Верх (5с)"); time.sleep(5); p1 = pyautogui.position()
        bot_tg.send_message(m.chat.id, "⬇️ Правый Низ (5с)"); time.sleep(5); p2 = pyautogui.position()
        x, y, w, h = min(p1.x, p2.x), min(p1.y, p2.y), abs(p1.x - p2.x), abs(p1.y - p2.y)
        if 'сундука' in m.text:
            areas['icon_area'] = [x, y, w, h]
            samples['icon'] = pyautogui.screenshot(region=(x, y, w, h))
        elif 'табло' in m.text: areas['btn_area'] = [x, y, w, h]
        elif 'таймера' in m.text: areas['timer_area'] = [x, y, w, h]
        bot_tg.send_message(m.chat.id, "✅ Настроено!")
    elif m.text == '📍 Точка клика':
        bot_tg.send_message(m.chat.id, "📍 Наведи на сундук (5с)"); time.sleep(5)
        points['icon_click'] = [pyautogui.position().x, pyautogui.position().y]
        bot_tg.send_message(m.chat.id, "✅ Точка сохранена!")
    elif m.text == '⏳ Время на стриме':
        km = types.InlineKeyboardMarkup(row_width=4)
        btns = [types.InlineKeyboardButton(f"{t}с", callback_data=f"w_{t}") for t in [5, 10, 15, 20, 25, 30, 60]]
        km.add(*btns); bot_tg.send_message(m.chat.id, "Интервал свайпа:", reply_markup=km)

@bot_tg.callback_query_handler(func=lambda call: call.data.startswith("w_"))
def callback_wait(call):
    global stream_wait_time
    stream_wait_time = int(call.data.split("_")[1])
    bot_tg.edit_message_text(f"✅ Установлено: {stream_wait_time}с", call.message.chat.id, call.message.message_id)

@bot_tg.message_handler(content_types=['photo'])
def ph(m):
    if m.caption and m.caption.lower() in FILE_MAP:
        inf = bot_tg.get_file(m.photo[-1].file_id)
        d = bot_tg.download_file(inf.file_path)
        with open(os.path.join(BASE_DIR, FILE_MAP[m.caption.lower()]), 'wb') as f: f.write(d)
        bot_tg.reply_to(m, f"✅ Шаблон '{m.caption}' обновлен!")

if __name__ == "__main__":
    root = tk.Tk()
    HunterGui(root)
    root.mainloop()