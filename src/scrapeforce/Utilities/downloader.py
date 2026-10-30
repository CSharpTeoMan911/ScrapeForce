from fake_useragent import UserAgent
import httpx


class __SilentLogger__:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class Downloader:
    def __init__(self):
        self.ua = UserAgent()

    def __generate_config__(
        self,
        format: int = 0,
        resolution: str = "1080",
        proxy: str = "",
        timeout: int = 10,
        retries: int = 3,
    ) -> dict:

        match format:
            case 0:
                format_string = f"bestvideo[height={resolution}][ext=webm]+bestaudio[ext=m4a]/bestvideo[height={resolution}]+bestaudio/best"

            case 1:
                format_string = "bestaudio"

        ydl_opts = {
            "format": format_string,
            "simulate": True,
            "user_agent": self.ua.random,
            "quiet": True,
            "no_warnings": True,
            "logger": __SilentLogger__(),
            "source_address": "0.0.0.0",
            "noplaylist": True,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "getcomments": False,
            "skip_download": True,
            "socket_timeout": timeout,  # Example: 5 seconds timeout for socket operations
            "retry_requests": 0,  # Number of times to retry network requests
            "retry_sleep": "2:4",  # Delay between retries for network requests
            "retries": retries,
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
            "extractor_args": {
                "youtube": {"player_client": ["default", "web_embedded"]}
            },
        }

        if proxy != "":
            ydl_opts["proxy"] = proxy

        return ydl_opts

    async def download_video(url: str, headers: dict, proxy: str):
        async with httpx.AsyncClient(
            proxy=proxy, timeout=None, follow_redirects=True
        ) as client, client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()

            async for chunk in response.aiter_bytes(65536):
                yield chunk

    def download_audio(self):
        pass
