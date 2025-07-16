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
from process_manager import ProcessManager
import subprocess
import threading


BROWSERS = ["browser.exe", "msedge.exe"]

# "chrome.exe"

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






def run_mitmproxy():
    """Запускает mitmproxy в отдельном процессе."""
    return subprocess.Popen(["python", "traffic_monitor.py"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        # creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    )

def monitor_browsers(mitm_state):
    """Отслеживает активные браузеры и завершает mitmproxy при их закрытии."""
    while mitm_state["active"]:
        current_pids = mitm_state["last_pids"].copy()

        # Проверяем, какие процессы всё ещё живы
        alive_pids = [
            pid for pid in current_pids
            if psutil.pid_exists(pid) and psutil.Process(pid).name().lower() in BROWSERS
        ]

        if not alive_pids:
            print("Нет активных браузеров. Останавливаем mitmproxy...")
            proc = mitm_state["process"]
            mitm_state["active"] = False
            mitm_state["last_pids"].clear()
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                print(f"Mitmporxy остановлен! PID: {proc.pid}")
            break

        time.sleep(2)


mitm_state = {
    "process": None,
    "active": False,
    "last_pids": set()
}


def system_windows_info(config) -> None:
    global mitm_state  # <-- Доступ к глобальному состоянию

    try:
        output_dir = config.get('Settings', 'output_dir')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "task4_data.json")

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                print("Файл содержит некорректный JSON. Создаём новый.")
                data = {}
        else:
            data = {}

        current_date = str(date.today())
        if current_date not in data:
            data[current_date] = {}

        current_time = str(datetime.now())
        if current_time not in data[current_date]:
            data[current_date][current_time] = []

        data_by_time = data[current_date][current_time]
        win32gui.EnumWindows(get_window_info, data_by_time)

        active_browser_pids = list({
            item["pid"] for item in data_by_time 
            if item.get("exe_name", "").lower() in BROWSERS
        })

        # Проверяем, какие PID всё ещё активны
        active_browser_pids = [
            pid for pid in active_browser_pids
            if psutil.pid_exists(pid) and psutil.Process(pid).name().lower() in BROWSERS
        ]

        # Если есть браузеры и MITM не запущен — запускаем
        if active_browser_pids and not mitm_state["active"]:
            print("Запускаем mitmproxy...")
            mitm_state["process"] = run_mitmproxy()
            mitm_state["active"] = True
            mitm_state["last_pids"] = set(active_browser_pids)

            # Запускаем мониторинг в отдельном потоке
            monitor_thread = threading.Thread(
                target=monitor_browsers,
                args=(mitm_state,),
                daemon=True
            )
            monitor_thread.start()

        elif active_browser_pids and mitm_state["active"]:
            # Если процессы браузеров изменились — обновляем список
            new_pids = set(active_browser_pids)
            if new_pids != mitm_state["last_pids"]:
                print(f"Обнаружены изменения в браузерах: {new_pids - mitm_state['last_pids']}")
                mitm_state["last_pids"] = new_pids

        elif not active_browser_pids and mitm_state["active"]:
            print("Браузеры закрыты. Ожидание завершения mitmproxy...")

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
