import os
import json
import win32com.client as dm
from datetime import datetime, date
import schedule
from task1 import load_config
import keyboard
import time


def get_connected_services(data_by_time):
    """ Функция для получения информации о служебных подключениях """

    wmi = dm.GetObject("winmgmts:")
    query = """
    SELECT * FROM Win32_PnPEntity 
    WHERE ConfigManagerErrorCode = 0
    """

    servises = wmi.ExecQuery(query)
    
    for service in servises:
        service_id = service.DeviceID.lower()
        service_name = service.Name
        service_desc = service.Description
        service_status = service.Status

        if service.Name:
            if (
                ("root_hub" in service_id or "pci" in service_id) or
                "Network" in service_name or
                ("dev" not in service_id and "Bluetooth" in service_name) or
                "HID" in service_name or
                "Audio" in service_name or
                "CardReader" in service_name
            ):

                connected_services = {
                    "name": service_name,
                    "id": service_id,
                    "description": service_desc,
                    "status": service_status
                }

                data_by_time.append(connected_services)


def get_connected_drives(data_by_time):
    """ Функция для получения ифнормации о дисках и флешках """

    wmi = dm.GetObject("winmgmts:")
    disks = wmi.ExecQuery("""
        SELECT * FROM Win32_DiskDrive 
        WHERE MediaLoaded=True
    """)
    
    for disk in disks:
        disk_name = disk.Caption
        if disk_name:
            disk_size = f"{int(disk.Size) // (1024 ** 3)} ГБ"
            disk_id = disk.DeviceID
            connected_disk = {
                "name": disk_name,
                "size": disk_size,
                "id": disk_id
            }

            data_by_time.append(connected_disk)


def get_active_bluetooth_devices(data_by_time):
    """ Функция для получения информации о bluetooth соединениях (только сопряженные) """

    wmi = dm.GetObject("winmgmts:")
    devices = wmi.ExecQuery("SELECT * FROM Win32_PNPEntity")

    for device in devices:
        if not device.Name:
            continue

        device_id = device.DeviceID.lower()

        # не учитываем службы bluetooth
        if "bthledevice" in device_id or "bthle" in device_id:
            continue

        if "dev" not in device_id:
            continue
        
        if "bth" in device_id or "bluetooth" in device_id:
            connected_bth_dev = {
                "name": device.Name,
                "id": device_id,
                "description": device.Description,
            }

            data_by_time.append(connected_bth_dev)


def get_active_usb_devices(data_by_time):
    """ Функция для получения информации о подключенни по usb (тут флешки тоже) """

    wmi = dm.GetObject("winmgmts:")
    hubs = wmi.ExecQuery("SELECT * FROM Win32_USBHub")
    
    for hub in hubs:
        device_id = hub.DeviceID.lower()

        if "root" in device_id: # не учитываем службы
            continue
        
        if hub.Status == "OK" and hub.Name:
            connected_usb_dev = {
                "name": hub.Name,
                "description": hub.Description,
                "id": hub.DeviceID
            }

            data_by_time.append(connected_usb_dev)


def get_devices_info(config):
    """ Функция для получения информации о подключенных устройствах """

    def check_key(key: str, dictionary: dict) -> None:
        if key not in dictionary:
            dictionary[key] = []
    
    try:
        output_dir = config.get('Settings', 'output_dir')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "task2_data.json")

        data = {}
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

        current_date = str(date.today())
        if current_date not in data:
            data[current_date] = {}

        current_time = str(datetime.now())
        if current_time not in data[current_date]:
            data[current_date][current_time] = {}

        data_by_time = data[current_date][current_time]

        # настройка сервисов
        services_key = "services"
        check_key(services_key, data_by_time)
        get_connected_services(data_by_time[services_key])

        # настройка дисков и флешек
        drives_key = "drives"
        check_key(drives_key, data_by_time)
        get_connected_drives(data_by_time[drives_key])

        # настройка bluetooth устройств
        bluetooth_key = "bluetooth"
        check_key(bluetooth_key, data_by_time)
        get_active_bluetooth_devices(data_by_time[bluetooth_key])

        # настройка usb устройств
        usb_key = "usb"
        check_key(usb_key, data_by_time)
        get_active_usb_devices(data_by_time[usb_key])

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(f"Данные сохранены в файл {file_path}")
    except Exception as e:
        print(f"Ошибка: {e}")


def main():
    config = load_config()
    interval = config.getint('Settings', 'interval')
    schedule.every(interval).minutes.do(get_devices_info, config)

    print(f"Интервал запуска программы в минутах: {interval}")
    get_devices_info(config) # первый раз, холодный старт

    while True:
        schedule.run_pending()
        if keyboard.is_pressed('q'):
            print("Завершение работы!")
            break

        time.sleep(0.1) # для уменьшения нагрузки на процессор, можно поставить и 1 секунду


if __name__ == "__main__":
    main()
