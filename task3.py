import requests
import os
from dotenv import load_dotenv
import win32api


load_dotenv()

TOKEN = os.getenv("token")
CHAT_ID = os.getenv("chat_id") # если открытый канал, то название
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def compare_dicts(prev: dict, curr: dict):
    """ Функция для сравнения словарей """

    common_keys = set(curr.keys()) & set(prev.keys())
    changes = {}

    for key in common_keys:
        if isinstance(prev[key], list) and isinstance(curr[key], list):
            list1 = prev[key]
            list2 = curr[key]

            # сохраняем по id
            dict_list1 = {item["id"]: item for item in list1}
            dict_list2 = {item["id"]: item for item in list2}
            
            # сравниваем по id
            added = [dict_list2[id] for id in dict_list2.keys() - dict_list1.keys()]
            removed = [dict_list1[id] for id in dict_list1.keys() - dict_list2.keys()]

            if added or removed:
                changes[key] = {
                    "added": added,
                    "removed": removed
                }
    return {
        "changes": changes
    }


def compare_data(data: dict, current_date: str) -> None:
    """ Функция для сравнения данных и отправки сообщения в тг """

    today = list(data[current_date].keys())
    all_data = list(data.keys())

    # текущие данные
    current_time = today[-1]
    current_data = data[current_date][current_time]

    # предыдущие данные
    prev_time = ""
    prev_data = current_data
    if len(today) < 2 and len(all_data) > 1: # если сегодня больше нет записей
        prev_time = list(data[all_data[-2]].keys())[-1]
        prev_data = data[all_data[-2]][prev_time]
    elif len(today) > 1: # если сегодня есть 2 и более записи
        prev_time = today[-2]
        prev_data = data[current_date][prev_time]
    else: # одна единственная запись
        prev_data = {"services": [], "drives": [], "bluetooth": [], "usb": []}

    result = compare_dicts(prev_data, current_data)

    if not len(result["changes"].items()):
        print("Нет изменений для сравнений!")

    for category, diff in result["changes"].items():
        if category == "services":
            continue
        
        if category == "usb": # не учитываем диски в usb
            for device in diff["added"]:
                if "запоминающее" in device["description"].lower():
                    diff["added"].remove(device)

            for device in diff["removed"]:
                if "запоминающее" in device["description"].lower():
                    diff["removed"].remove(device)
            

        devices_added = "" # парсим добавленные устройства
        for device in diff["added"]:
            devices_added += f"Имя: {device['name']}\n" + f"Id: <code>{device['id']}</code>\n\n"

        devices_removed = "" # парсим удаленные устройства
        for device in diff["removed"]:
            devices_removed += f"Имя: {device['name']}\n" + f"Id: <code>{device['id']}</code>\n\n"

        count_added = len(diff["added"])
        count_removed = len(diff["removed"])

        msg = (
            f"Имя машины: {win32api.GetComputerName()}\n"
            f"Изменения в категории: <b>{category}</b>:\n"
            f"Добавлено устройств: {count_added}\n"
            f"{devices_added}"
            f"Удалено устройств: {count_removed}\n"
            f"{devices_removed}"
        )

        if count_added or count_removed:
            send_message(url, msg)
    
    return
        

def send_message(url: str, message: str):
    """ Функция для отправки сообщения через бота """

    params = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    response = requests.post(url, json=params)
    print(response.json())
