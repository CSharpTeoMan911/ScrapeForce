import random
import threading
import time
from concurrent import futures

import requests
import yt_dlp as ytd
from fake_useragent import UserAgent


class __SilentLogger__:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class __ExtractProxyUrls__:
    min_latency_ms = 500
    uptime_percent = 70

    def __init__(self, min_latency_ms: int = 500, uptime_percent: int = 70):
        if uptime_percent > 100:
            raise Exception(  # noqa: TRY002
                "Error: You cannot have an uptime greater than 100%. (e.g. 0.1 = 10%)"
            )
        elif uptime_percent < 0:
            raise Exception(  # noqa: TRY002
                "Error: You cannot have an uptime smaller than 0%. (e.g. 0.1 = 10%)"
            )
        elif min_latency_ms < 0:
            raise Exception(  # noqa: TRY002
                "Error: You cannot have a latency smaller than 0. (e.g. 1 = 1ms)"
            )
        else:
            self.min_latency = min_latency_ms
            self.uptime_percent = uptime_percent

    def get_hproxy_urls(self, stop_event=None, timeout: int = 10) -> list:
        if stop_event is not None and stop_event.is_set():
            return []

        r = requests.get(
            "https://hproxy.com/api/proxy-list",
            params={
                "format": "json",
                "protocol": "http,socks5",
                "min_uptime_pct": self.uptime_percent,
                "max_latency_ms": self.min_latency,
                "sort": "uptime",
            },
            timeout=timeout,
        )
        r.raise_for_status()
        if stop_event is not None and stop_event.is_set():
            return []

        proxies_json = r.json()
        return [rf"{x['protocols'][0]}://{x['ip']}" for x in proxies_json]

    def get_roundproxies_urls(
        self, limit=1000, speed="fast", stop_event=None, timeout: int = 10
    ) -> list:
        page = 1
        VALUE = []
        while (
            (stop_event is None or not stop_event.is_set())
            and len(VALUE) < limit
        ):
            response = requests.get(
                f"https://roundproxies.com/api/get-free-proxies?limit=100&page={page}&sort_by=lastChecked&sort_type=desc&speed={speed}&uptime=high",
                timeout=timeout,
            )
            response.raise_for_status()
            if stop_event is not None and stop_event.is_set():
                return []

            BUFFER = [
                f"{x['protocols'][0]}://{x['ip']}"
                for x in response.json()["data"]
            ]
            if len(BUFFER) > 0 and len(VALUE) < limit:
                VALUE.extend(BUFFER)
                page += 1
            else:
                break
        if stop_event is not None and stop_event.is_set():
            return []
        return VALUE

    def get_proxifly_urls(self, stop_event=None, timeout: int = 10) -> list:
        if stop_event is not None and stop_event.is_set():
            return []

        response = requests.get(
            "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.json",
            timeout=timeout,
        )
        response.raise_for_status()
        if stop_event is not None and stop_event.is_set():
            return []

        return [x["proxy"] for x in response.json()]

    def get_proxyscrape_urls(self, stop_event=None, timeout: int = 10) -> list:
        if stop_event is not None and stop_event.is_set():
            return []

        response = requests.get(
            "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/all/data.json",
            timeout=timeout,
        )
        response.raise_for_status()
        if stop_event is not None and stop_event.is_set():
            return []

        return [
            f"{x['protocol']}://{x['ip']}"
            for x in response.json()
            if x["uptime_percent"] > 70 and x["anonymity"] == "elite"
        ]


class ProxyTest:
    def __init__(self):
        self.main_thread: threading.Thread | None = None
        self.proxies_to_verify = 0
        self.stop_proxy_test = threading.Event()
        self.proxy_test_started = threading.Event()
        self.proxies_available = threading.Event()
        self.ua = UserAgent(platforms="mobile", os="Android")
        self.valid_urls: dict[float, str] = {}
        self._futures: set[futures.Future[None]] = set()
        self._lock = threading.Lock()

    def __test_proxy__(self, proxy_url: str, timeout: int = 10):
        try:
            if not self.stop_proxy_test.is_set():
            
                youtube_test_url = (
                    "https://www.youtube.com/watch?v=x3GAazGeqwc"
                )
                # Extract protocol from proxy_url for dynamic proxy dictionary


                actual_user_agent = self.ua.random

                ydl_opts = {
                    "format": "bestvideo+bestaudio",
                    "simulate": True,
                    "user_agent": actual_user_agent,
                    "quiet": True,
                    "no_warnings": True,
                    "logger": __SilentLogger__(),
                    "source_address": "0.0.0.0",
                    "noplaylist": True,
                    "writesubtitles": False,
                    "writeautomaticsub": False,
                    "getcomments": False,
                    "proxy": proxy_url,
                    "skip_download": True,
                    "socket_timeout": timeout,  # Example: 5 seconds timeout for socket operations
                    "retry_requests": 0,  # Number of times to retry network requests
                    "retry_sleep": "2:4",  # Delay between retries for network requests
                    "retries": 0,
                    "extractor_retries": 0,
                    "fragment_retries": 0,  # Number of times to retry downloading individual fragments
                    "skip_unavailable_fragments": True,  # Skip fragments if they're unavailable
                    "http_chunk_size": 10 * 1024 * 1024,
                    "force_ipv4": True,
                    "http2": False,
                    "js_runtimes": {
                        "deno": {
                            "path": None
                        }  # Forces yt-dlp to drop the default pre-emption check
                    },
                    "extractor_args": {"youtube": {"player_client": ["default", 'web_embedded']}},
                }

                try:
                    with ytd.YoutubeDL(ydl_opts) as extractor:
                        
                        start = time.perf_counter()
                        response = extractor.extract_info(youtube_test_url, download=False)
                        
                        
                        if type(response) == dict:
                            print(response)
                            self.proxies_available.set()
                            latency = (time.perf_counter() - start) * 1000
                            self.valid_urls[latency] = proxy_url

                except Exception as e:  # noqa: BLE001, S110
                    pass

        except KeyboardInterrupt:
            self.stop_proxy_test.set()
        finally:
            with self._lock:
                self.proxies_to_verify -= 1

    def __proxy_testing_thread__(
        self, min_latency_ms: int = 500, min_uptime: int = 70, timeout: int = 10
    ):
        executor = futures.ThreadPoolExecutor(max_workers=10)
        last_refresh = 0.0

        try:
            proxy_urls_extractor = __ExtractProxyUrls__(
                min_latency_ms=min_latency_ms, uptime_percent=min_uptime
            )

            while not self.stop_proxy_test.is_set():
                with self._lock:
                    batch_in_progress = self.proxies_to_verify > 0

                if batch_in_progress:
                    self.stop_proxy_test.wait(0.2)
                    continue

                now = time.monotonic()
                if (
                    self.proxy_test_started.is_set()
                    and now - last_refresh < 60 * 60
                ):
                    self.stop_proxy_test.wait(
                        min(1.0, 60 * 60 - (now - last_refresh))
                    )
                    continue

                proxies = []
                for get_urls in (
                    proxy_urls_extractor.get_hproxy_urls,
                    proxy_urls_extractor.get_proxifly_urls,
                    proxy_urls_extractor.get_proxyscrape_urls,
                    proxy_urls_extractor.get_roundproxies_urls,
                ):
                    if self.stop_proxy_test.is_set():
                        break
                    proxies.extend(
                        get_urls(stop_event=self.stop_proxy_test, timeout=timeout)
                    )

                if self.stop_proxy_test.is_set():
                    break
                if not proxies:
                    self.stop_proxy_test.wait(5)
                    continue

                with self._lock:
                    self.proxies_to_verify = len(proxies)
                self.proxy_test_started.set()
                last_refresh = time.monotonic()
                random.shuffle(proxies)

                pending = set()
                for proxy_url in proxies:
                    with self._lock:
                        if self.stop_proxy_test.is_set():
                            break
                        future = executor.submit(
                            self.__test_proxy__, proxy_url=proxy_url, timeout=timeout
                        )
                        self._futures.add(future)
                    pending.add(future)

                while pending:
                    done, pending = futures.wait(
                        pending,
                        timeout=0.2,
                        return_when=futures.FIRST_COMPLETED,
                    )
                    for future in done:
                        with self._lock:
                            self._futures.discard(future)
                        if not future.cancelled():
                            try:
                                future.result()
                            except Exception as e:  # noqa: BLE001
                                print(f"Proxy test worker failed: {e}")

                    if self.stop_proxy_test.is_set():
                        for future in pending:
                            future.cancel()
        finally:
            self.stop_proxy_test.set()
            with self._lock:
                pending_futures = tuple(self._futures)
            for future in pending_futures:
                future.cancel()
            executor.shutdown(wait=True, cancel_futures=True)
            with self._lock:
                self._futures.clear()

    def test_proxies(
        self, min_latency_ms: int = 500, min_uptime: int = 70, timeout: int = 10
    ):
        if self.main_thread is not None and self.main_thread.is_alive():
            raise RuntimeError("Proxy testing is already running")

        self.stop_proxy_test.clear()
        self.proxy_test_started.clear()
        self.proxies_available.clear()
        with self._lock:
            self.proxies_to_verify = 0

        self.main_thread = threading.Thread(
            target=self.__proxy_testing_thread__,
            args=(min_latency_ms, min_uptime, timeout),
        )
        self.main_thread.start()

    def shutdown_test(self):
        self.stop_proxy_test.set()
        with self._lock:
            pending_futures = tuple(self._futures)
        for future in pending_futures:
            future.cancel()

        thread = self.main_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join()
            
    def are_proxies_available(self) -> bool:
        return self.proxies_available.is_set()
