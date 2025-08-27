import httpx
import pytest

pytestmark = pytest.mark.asyncio


async def test_index_page_loads(page_url: str):
    """
    Performs an end-to-end test on the index page ('/').
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(page_url)

    assert response.status_code == 200
    assert "<h1>Welcome to your new Django project!</h1>" in response.text
    assert "<title>Django Project</title>" in response.text
