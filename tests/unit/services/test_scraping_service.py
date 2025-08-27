import socket
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests import Response

from apps.gist.services.scraping_service import ScrapingService


class TestScrapingService:
    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com",
            "https://example.com/path?query=1",
            "http://example.com:8080",
            "https://example.com/path#section",
        ],
    )
    def test_validate_url_valid(self, url):
        # When: URL をバリデーション
        # Then: 例外が発生しない
        ScrapingService.validate_url(url)

    @pytest.mark.parametrize(
        "url, expected_error_message",
        [
            ("ftp://example.com", "URLは http/https のみ対応しています。"),
            ("http://", "URLのホスト名が不正です。"),
            ("just-a-string", "URLは http/https のみ対応しています。"),
            ("file:///etc/passwd", "URLは http/https のみ対応しています。"),
            ("http:///path", "URLのホスト名が不正です。"),
        ],
    )
    def test_validate_url_invalid(self, url, expected_error_message):
        # When: 不正な URL をバリデーション
        # Then: ValueError が発生する
        with pytest.raises(ValueError, match=expected_error_message):
            ScrapingService.validate_url(url)

    @patch("apps.gist.services.scraping_service.socket.getaddrinfo")
    def test_validate_url_private_host(self, mock_getaddrinfo):
        # Given: localhost はプライベートホスト
        url = "http://localhost"
        mock_getaddrinfo.return_value = [(socket.AF_INET, 0, 0, "", ("127.0.0.1", 80))]

        # When: localhost の URL をバリデーション
        # Then: ValueError が発生する
        with pytest.raises(ValueError, match="指定のホストは許可されていません。"):
            ScrapingService.validate_url(url)

    @patch("apps.gist.services.scraping_service.socket.getaddrinfo")
    def test_validate_url_public_host(self, mock_getaddrinfo):
        # Given: example.com はパブリックホスト
        url = "http://example.com"
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, 0, 0, "", ("93.184.216.34", 80))
        ]

        # When: example.com の URL をバリデーション
        # Then: 例外が発生しない
        ScrapingService.validate_url(url)

    @patch("apps.gist.services.scraping_service.requests.get")
    def test_scrape_success(self, mock_get):
        # Given: 正常な HTML レスポンスを返す mock
        url = "http://example.com"
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <header>Header</header>
                <nav>Nav</nav>
                <main>
                    <h1>Title</h1>
                    <p>This is a paragraph.</p>
                </main>
                <aside>Aside</aside>
                <footer>Footer</footer>
                <script>alert('hello');</script>
                <style>p { color: red; }</style>
            </body>
        </html>
        """
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = html_content.encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # When: スクレイピングを実行
        with patch(
            "apps.gist.services.scraping_service.socket.getaddrinfo",
            return_value=[(socket.AF_INET, 0, 0, "", ("93.184.216.34", 0))],
        ):
            result = ScrapingService.scrape(url)

        # Then: 不要なタグが除去されたテキストが返る
        assert result == "Title This is a paragraph."
        mock_get.assert_called_once()
        # requests.get の引数を検証
        _, kwargs = mock_get.call_args
        # 呼び出し URL と UA の妥当性を追加検証
        assert mock_get.call_args[0][0] == url
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == (10, 30)
        assert "User-Agent" in kwargs["headers"]
        ua = kwargs["headers"].get("User-Agent", "")
        assert "Mozilla/5.0" in ua
        mock_response.raise_for_status.assert_called_once()

    @patch("apps.gist.services.scraping_service.requests.get")
    def test_scrape_request_exception(self, mock_get):
        # Given: requests.RequestException を発生させる mock
        url = "http://example.com"
        mock_get.side_effect = requests.RequestException("Test error")

        # When: スクレイピングを実行
        # Then: ValueError が発生する
        with pytest.raises(
            ValueError, match="コンテンツ取得に失敗しました: Test error"
        ):
            ScrapingService.scrape(url)

    @patch("apps.gist.services.scraping_service.requests.get")
    def test_scrape_non_html_content(self, mock_get):
        # Given: 非 HTML コンテンツ (e.g. PDF) を返す mock
        url = "http://example.com/file.pdf"
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4..."
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # When: スクレイピングを実行
        result = ScrapingService.scrape(url)

        # Then: 空文字列が返る
        assert result == ""
        mock_response.raise_for_status.assert_called_once()

    @patch("apps.gist.services.scraping_service.requests.get")
    def test_scrape_text_plain_returns_empty(self, mock_get):
        url = "http://example.com/raw.txt"
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        mock_resp.content = b"plain text"
        mock_resp.headers = {"Content-Type": "text/plain"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert ScrapingService.scrape(url) == ""
        mock_resp.raise_for_status.assert_called_once()

    @patch("apps.gist.services.scraping_service.socket.getaddrinfo")
    def test_validate_url_ipv6_loopback_rejected(self, mock_getaddrinfo):
        url = "http://localhost"
        mock_getaddrinfo.return_value = [(socket.AF_INET6, 0, 0, "", ("::1", 0, 0, 0))]
        with pytest.raises(ValueError, match="指定のホストは許可されていません。"):
            ScrapingService.validate_url(url)

    @patch("apps.gist.services.scraping_service.requests.get")
    def test_scrape_no_body(self, mock_get):
        # Given: body タグのない HTML を返す mock
        url = "http://example.com"
        html_content = "<html><head><title>Test</title></head></html>"
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = html_content.encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # When: スクレイピングを実行
        result = ScrapingService.scrape(url)

        # Then: 空文字列が返る
        assert result == ""
        mock_response.raise_for_status.assert_called_once()

    @patch("apps.gist.services.scraping_service.requests.get")
    def test_scrape_http_error(self, mock_get):
        url = "http://example.com/notfound"
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 404
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.content = b"not found"
        mock_resp.raise_for_status.side_effect = requests.HTTPError(
            "404 Client Error: Not Found for url"
        )
        mock_get.return_value = mock_resp

        with pytest.raises(
            ValueError, match="コンテンツ取得に失敗しました: 404 Client Error"
        ):
            ScrapingService.scrape(url)

    @patch("apps.gist.services.scraping_service.socket.getaddrinfo")
    def test_validate_url_ipv6_linklocal_with_zone_rejected(self, mock_getaddrinfo):
        url = "http://example.com"
        mock_getaddrinfo.return_value = [
            (socket.AF_INET6, 0, 0, "", ("fe80::1%lo0", 0, 0, 0))
        ]
        with pytest.raises(ValueError, match="指定のホストは許可されていません。"):
            ScrapingService.validate_url(url)
