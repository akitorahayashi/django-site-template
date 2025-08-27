import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class ScrapingService:
    @staticmethod
    def validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URLは http/https のみ対応しています。")
        if not parsed.hostname:
            raise ValueError("URLのホスト名が不正です。")
        if ScrapingService._is_private_host(parsed.hostname):
            raise ValueError("指定のホストは許可されていません。")

    @staticmethod
    def _is_private_host(host: str) -> bool:
        addrs = set()
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                for info in socket.getaddrinfo(host, None, family):
                    addrs.add(info[4][0])
            except socket.gaierror:
                continue
        for addr in addrs:
            ip = ipaddress.ip_address(addr.split("%")[0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                return True
        return False

    @staticmethod
    def scrape(url: str, timeout=(10, 30)) -> str:
        ScrapingService.validate_url(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(
                url, headers=headers, timeout=timeout, allow_redirects=False
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"コンテンツ取得に失敗しました: {e}") from e

        # 明らかに非 HTML のレスポンスは早期リターン
        ctype = (response.headers.get("Content-Type") or "").lower()
        if not ("html" in ctype or ctype.startswith("text/")):
            return ""

        soup = BeautifulSoup(response.content, "html.parser")
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            element.decompose()
        if soup.body:
            return soup.body.get_text(separator=" ", strip=True)
        return ""
