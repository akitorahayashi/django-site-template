import time
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# --- Constants ---
DEFAULT_HEALTH_CHECK_TIMEOUT = 5
DEFAULT_SUMMARIZE_CONNECT_TIMEOUT = 5
DEFAULT_SUMMARIZE_READ_TIMEOUT = 60
DEFAULT_HEALTH_CHECK_TTL = 30

# Load timeouts from settings, with defaults
HEALTH_CHECK_TIMEOUT = getattr(
    settings, "SUMMARY_HEALTH_CHECK_TIMEOUT", DEFAULT_HEALTH_CHECK_TIMEOUT
)
SUMMARIZE_CONNECT_TIMEOUT = getattr(
    settings, "SUMMARY_SUMMARIZE_CONNECT_TIMEOUT", DEFAULT_SUMMARIZE_CONNECT_TIMEOUT
)
SUMMARIZE_READ_TIMEOUT = getattr(
    settings, "SUMMARY_SUMMARIZE_READ_TIMEOUT", DEFAULT_SUMMARIZE_READ_TIMEOUT
)
HEALTH_CHECK_TTL = getattr(
    settings, "SUMMARY_HEALTH_CHECK_TTL", DEFAULT_HEALTH_CHECK_TTL
)


class SummarizationServiceError(Exception):
    """要約サービスで発生したエラーのベース例外クラス"""

    pass


class SummarizationService:
    def __init__(self):
        if not settings.PVT_LLM_API_URL:
            raise ImproperlyConfigured("PVT_LLM_API_URL is not configured.")
        self.api_base_url = settings.PVT_LLM_API_URL
        self._last_health_check_time = 0

    def _build_url(self, path: str) -> str:
        """Builds a full URL from a path segment."""
        base = self.api_base_url.rstrip("/") + "/"
        return urljoin(base, path)

    def _health_check(self):
        """
        連携先のLLM APIのヘルスチェックを行う。
        成功結果はTTL秒間キャッシュする。
        正常でない場合は SummarizationServiceError を送出する。
        """
        if time.monotonic() - self._last_health_check_time < HEALTH_CHECK_TTL:
            return

        health_check_url = self._build_url("health")
        try:
            response = requests.get(health_check_url, timeout=HEALTH_CHECK_TIMEOUT)
            if not response.ok:
                snippet = response.text[:200]
                raise SummarizationServiceError(
                    f"LLM API is unhealthy. Status: {response.status_code}, Body: {snippet}"
                )
            self._last_health_check_time = time.monotonic()
        except requests.exceptions.RequestException as e:
            raise SummarizationServiceError(f"Failed to connect to LLM API: {e}") from e

    def summarize(self, text: str, max_chars: int | None = None) -> str:
        if not text or not text.strip():
            return ""

        if max_chars is None:
            if not hasattr(settings, "SUMMARY_MAX_CHARS"):
                raise AttributeError("settings.SUMMARY_MAX_CHARS is not defined.")
            max_chars = settings.SUMMARY_MAX_CHARS

        self._health_check()

        truncated_text = text[:max_chars]
        prompt = f"""以下のテキストを日本語で要約してください。

テキスト:
{truncated_text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""

        api_url = self._build_url("api/v1/generate")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {"prompt": prompt, "stream": False}

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=(SUMMARIZE_CONNECT_TIMEOUT, SUMMARIZE_READ_TIMEOUT),
            )
            response.raise_for_status()

            response_json = response.json()
            if "response" not in response_json:
                raise SummarizationServiceError(
                    "APIレスポンスに'response'キーが含まれていません。"
                )

            return response_json["response"]

        except requests.exceptions.RequestException as e:
            raise SummarizationServiceError(f"APIへの接続に失敗しました: {e}") from e
        except ValueError:
            raise SummarizationServiceError(
                "APIレスポンスのJSONデコードに失敗しました。"
            )
