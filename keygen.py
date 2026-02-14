import uuid, json, os


def generate_key(username):
    new_key = str(uuid.uuid4())[:8]  # короткий ключ из 8 символов
    data = {}
    if os.path.exists('keys.json'):
        with open('keys.json', 'r') as f: data = json.load(f)

    data[new_key] = {"user": username, "active": True}
    with open('keys.json', 'w') as f: json.dump(data, f)
    print(f"Ключ для {username} создан: {new_key}")


name = input("Введите имя пользователя: ")
generate_key(name)