import json
import os
import time
import win32gui
import win32process
import schedule
import keyboard
from datetime import datetime, date
from common import load_config
import psutil
from set_monitoring import check_and_set_monitoring


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

    window_title = win32gui.GetWindowText(hwnd)

    if win32gui.IsWindowVisible(hwnd) and window_title:
        window_class = win32gui.GetClassName(hwnd)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        exe_name = process.name().lower()

        window_data = {
            "handler": hwnd,
            "title": window_title,
            "class": window_class,
            "size": f"Size: {width}x{height}",
            "pid": pid,
            "process_name": process.name(),
            "exe_name": exe_name
        }

        data.append(window_data)
    return True


mitm_state = { # фиксируем состояние между вызовами функции
    "process": None,
    "active": False,
    "last_pids": set()
}


def system_windows_info(config) -> None:
    """ Функция для получения информации об окнах и о запросаз браузеров """

    global mitm_state # так как меняем, указываем global

    try:
        # создаем диеркторию, если нужно
        output_dir = config.get('Settings', 'output_dir')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "task4_data.json")

        # если файл существует, то берем данные из него, иначе пишем с нуля
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                print("Файл содержит некорректный JSON. Создаём новый.")
                data = {}
        else:
            data = {}

        # достаем текущую дату и время
        current_date = str(date.today())
        if current_date not in data:
            data[current_date] = {}

        current_time = str(datetime.now())
        if current_time not in data[current_date]:
            data[current_date][current_time] = []

        # получаем данные об открытых окнах
        data_by_time = data[current_date][current_time]
        win32gui.EnumWindows(get_window_info, data_by_time)

        # проверяем и запускаем мониторинг при наличии браузеров
        check_and_set_monitoring(mitm_state=mitm_state, data_by_time=data_by_time)

        # Сохраняем данные
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

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
