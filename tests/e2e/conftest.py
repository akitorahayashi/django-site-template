import os
import subprocess
import time
from typing import Generator

import httpx
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session")
def page_url() -> str:
    """
    Returns the URL of the page to be tested.
    """
    # This default must match the default in docker-compose.yml
    host_port = os.getenv("HOST_PORT", "50080")
    return f"http://localhost:{host_port}/"


@pytest.fixture(scope="session", autouse=True)
def e2e_setup(page_url: str) -> Generator[None, None, None]:
    """
    Manages the lifecycle of the application for end-to-end testing.
    """
    # Load environment variables from .env.test
    load_dotenv(".env.test")

    # Determine if sudo should be used based on environment variable
    # This allows `SUDO=true make e2e-test` to work as expected.
    use_sudo = os.getenv("SUDO") == "true"
    docker_command = ["sudo", "docker"] if use_sudo else ["docker"]

    # Start services using docker-compose
    print("\n🚀 Starting E2E services...")
    compose_up_command = docker_command + [
        "compose",
        "-f",
        "docker-compose.yml",
        "--env-file",
        ".env.test",
        "--project-name",
        "template-test",
        "up",
        "-d",
        "--build",
    ]
    subprocess.run(compose_up_command, check=True)

    # Teardown command to be used both on success and failure
    compose_down_command = docker_command + [
        "compose",
        "--project-name",
        "template-test",
        "down",
        "--remove-orphans",
    ]

    # Health Check
    start_time = time.time()
    timeout = 120
    is_healthy = False
    print(f"Polling health check at {page_url}...")
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(page_url, timeout=5)
            if response.status_code == 200:
                print("✅ Application is healthy!")
                is_healthy = True
                break
        except httpx.RequestError:
            print("⏳ Application not yet healthy, retrying...")
            time.sleep(5)

    if not is_healthy:
        log_command = docker_command + [
            "compose",
            "--project-name",
            "template-test",
            "logs",
            "web",
        ]
        subprocess.run(log_command)
        # Ensure teardown on failure to avoid lingering containers
        print("\n🛑 Stopping E2E services due to health check failure...")
        subprocess.run(compose_down_command, check=True)
        pytest.fail(f"Application did not become healthy within {timeout} seconds.")

    yield

    # Stop services
    print("\n🛑 Stopping E2E services...")
    subprocess.run(compose_down_command, check=True)
