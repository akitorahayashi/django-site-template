import os

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv(".env.test")

pytestmark = pytest.mark.asyncio


async def test_index_page_loads():
    """
    Performs an end-to-end test on the index page ('/').
    """
    host_port = os.getenv("HOST_PORT", "8000")
    index_url = f"http://localhost:{host_port}/"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(index_url)

    assert response.status_code == 200
    assert "<h1>Enter URL to Scrape</h1>" in response.text
    assert "<title>Web Page Scraper</title>" in response.text
