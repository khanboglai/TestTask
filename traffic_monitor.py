import json
import asyncio
from mitmproxy.http import HTTPFlow
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options


class TrafficDumper:
    def __init__(self, output_file="traffic.json"):
        self.output_file = output_file
        self.traffic = []

    def _is_user_request(self, flow: HTTPFlow) -> bool:
        """ Фильтрация пользовательских запросов """
        headers = flow.request.headers

        if (
            headers.get("Sec-Fetch-Dest") in ("script", "style", "image", "font", "no-cors") or
            "google-analytics.com" in flow.request.host or
            "doubleclick.net" in flow.request.host or
            flow.request.method == "OPTIONS"
        ):
            return False

        return (
            headers.get("Sec-Fetch-Mode") == "navigate" and 
            headers.get("Sec-Fetch-Dest") == "document"
        )

    def request(self, flow: HTTPFlow) -> None:
        """ Метод для получения и сохранения запросов пользователя """
        if self._is_user_request(flow):
            req = {
                "method": flow.request.method,
                "url": flow.request.url,
                "headers": dict(flow.request.headers),
                "data": flow.request.text if flow.request.text else None,
                "timestamp": flow.request.timestamp_start
            }
            self.traffic.append(req)
            self._dump_to_file()

            print(f"Logged user request: {flow.request.method} {flow.request.url}")

    def _dump_to_file(self) -> None:
        """ Запись в JSON файл """
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.traffic, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving to file: {e}")


async def start_proxy():
    # Создаем опции напрямую через Options
    opts = Options(
        listen_host="0.0.0.0",
        listen_port=8080,
        mode=["regular"]
    )
    
    master = DumpMaster(options=opts)
    master.addons.add(TrafficDumper())  # Добавляем наш аддон

    print("MITM proxy запущен на порту 8080...")
    try:
        await master.run()
    except KeyboardInterrupt:
        print("Shutting down proxy...")


if __name__ == "__main__":
    asyncio.run(start_proxy())