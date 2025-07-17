""" Функции для настройки мониторинга запросов браузеров """

import subprocess
import psutil
import time
from set_proxy import *
import threading


BROWSERS = ["browser.exe", "msedge.exe", "chrome.exe"]


def run_mitmproxy():
    """ Функция для запуска mitmproxy в отдельном процессе """

    return subprocess.Popen(["python", "traffic_monitor.py"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        # creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    )


def monitor_browsers(mitm_state) -> None:
    """ Функция для отслеживания браузеров """

    while mitm_state["active"]:
        current_pids = mitm_state["last_pids"].copy()

        # Проверяем, какие процессы всё ещё живы
        alive_pids = [
            pid for pid in current_pids
            if psutil.pid_exists(pid) and psutil.Process(pid).name().lower() in BROWSERS
        ]

        if not alive_pids:
            print("Нет активных браузеров. Останавливаем mitmproxy...")
            disable_windows_proxy()
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


def check_and_set_monitoring(mitm_state, data_by_time) -> None:
    """ Функция для проверки наличия браузеров и запуска мониторинга """

    active_browser_pids = list({
        item["pid"] for item in data_by_time 
        if item.get("exe_name", "").lower() in BROWSERS
    })

    # проверяем, какие PID всё ещё активны
    active_browser_pids = [
        pid for pid in active_browser_pids
        if psutil.pid_exists(pid) and psutil.Process(pid).name().lower() in BROWSERS
    ]

    # если есть браузеры и MITM не запущен — запускаем
    if active_browser_pids and not mitm_state["active"]:
        proxy, _ = get_windows_proxy()
        if not proxy:
            set_windows_proxy()
            
        print("Запускаем mitmproxy...")
        mitm_state["process"] = run_mitmproxy()
        mitm_state["active"] = True
        mitm_state["last_pids"] = set(active_browser_pids)

        # запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(
            target=monitor_browsers,
            args=(mitm_state,),
            daemon=True
        )
        monitor_thread.start()

    elif active_browser_pids and mitm_state["active"]:
        # если процессы браузеров изменились — обновляем список
        new_pids = set(active_browser_pids)
        if new_pids != mitm_state["last_pids"]:
            print(f"Обнаружены изменения в браузерах: {new_pids - mitm_state['last_pids']}")
            mitm_state["last_pids"] = new_pids

    elif not active_browser_pids and mitm_state["active"]:
        print("Браузеры закрыты. Ожидание завершения mitmproxy...")
    