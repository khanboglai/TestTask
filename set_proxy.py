""" Работа с прокси в Windows """

import winreg as _winreg


def set_windows_proxy(proxy_server="127.0.0.1:8080"):
    """
    Устанавливает системный прокси в Windows.
    :param proxy_server: Адрес прокси в формате "host:port"
    """

    INTERNET_SETTINGS = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
        0, _winreg.KEY_ALL_ACCESS
    )

    # включаем прокси
    _winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyEnable', 0, _winreg.REG_DWORD, 1)

    # устанавливаем адрес прокси
    _winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyServer', 0, _winreg.REG_SZ, proxy_server)

    # (Опционально) можно указать список исключений (например, локальные адреса)
    _winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyOverride', 0, _winreg.REG_SZ, 'localhost;127.0.0.1;.local')

    _winreg.CloseKey(INTERNET_SETTINGS)
    print(f"Прокси включен: {proxy_server}")


def disable_windows_proxy() -> None:
    """ Функция для отключения системного прокси """

    INTERNET_SETTINGS = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
        0, _winreg.KEY_ALL_ACCESS
    )

    _winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyEnable', 0, _winreg.REG_DWORD, 0)
    _winreg.CloseKey(INTERNET_SETTINGS)
    print("Прокси выключен")


def get_windows_proxy():
    """ Функция для проверки активности прокси """

    INTERNET_SETTINGS = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
        0, _winreg.KEY_READ
    )

    try:
        proxy_enable, _ = _winreg.QueryValueEx(INTERNET_SETTINGS, 'ProxyEnable')
        proxy_server, _ = _winreg.QueryValueEx(INTERNET_SETTINGS, 'ProxyServer')
    except FileNotFoundError:
        proxy_enable = 0
        proxy_server = ""

    _winreg.CloseKey(INTERNET_SETTINGS)
    print(f"ProxyEnable: {proxy_enable}, ProxyServer: {proxy_server}")
    return bool(proxy_enable), proxy_server


if __name__ == "__main__":
    set_windows_proxy("127.0.0.1:8080")
    # disable_windows_proxy()
