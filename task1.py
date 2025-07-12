import json
import os
import time
import win32gui
import schedule
import keyboard
from datetime import datetime
from configparser import ConfigParser


CONFIG_FILE = "config.cfg"
DEFAULT_CONF = {
    'Settings': {
        'output_dir': 'windows_data',
        'interval': '1'
    }
}


def load_config():
    """ Функция для заргузки файла конфигурации """
    
    config = ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config.read_dict(DEFAULT_CONF)

        with open(CONFIG_FILE, 'w') as file:
            config.write(file)
    else:
        config.read(CONFIG_FILE)
    return config


def get_window_info(hwnd, data):
    """ Callback функция для получения информации об окне """

    class_name = win32gui.GetClassName(hwnd)

    # можно добавить классы окон, которые нужно искоючить из рассмотрения
    # в текущей реализации собираем данные только об окнах, которые открывал пользователь
    system_classes = [
    "Windows.UI.Core.CoreWindow",  # Системные окна
    "CEF-OSC-WIDGET",              # Оверлей NVIDIA
    "Progman",                     # Program Manager
    "ApplicationFrameWindow",
    ]

    if class_name in system_classes:
        return True # переход к следующему окну

    current_time = str(datetime.now())
    window_title = win32gui.GetWindowText(hwnd)

    if win32gui.IsWindowVisible(hwnd) and window_title:
        window_class = win32gui.GetClassName(hwnd)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        window_data = {
            "handler": hwnd,
            "title": window_title,
            "class": window_class,
            "size": f"Size: {width}x{height}",
            "time": current_time
        }

        if "data" not in data:
            data["data"] = []

        data["data"].append(window_data)
    return True


def system_windows_info(config) -> None:
    """ Функция для получения информации о всех открытых окнах системы """

    try:
        output_dir = config.get('Settings', 'output_dir')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "task1_data.json")

        data = {}
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data["data"] = json.load(file)

        win32gui.EnumWindows(get_window_info, data)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data["data"], file, indent=4, ensure_ascii=False)

        print(f"Данные сохранены в файл {file_path}")
    except Exception as e:
        print(f"Ошибка: {e}")


def main():
    config = load_config()
    interval = config.getint('Settings', 'interval')
    schedule.every(interval).minutes.do(system_windows_info, config)

    print(f"Интервал запуска программы в минутах: {interval}")
    system_windows_info(config) # первый раз, холодный старт

    while True:
        schedule.run_pending()
        if keyboard.is_pressed('q'):
            print("Завершение работы!")
            break

        time.sleep(0.1) # для уменьшения нагрузки на процессор, можно поставить и 1 секунду


if __name__ == "__main__":
    main()
