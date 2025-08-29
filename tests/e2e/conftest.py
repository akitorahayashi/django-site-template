import os
import subprocess
import time
from typing import Generator

import httpx
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set environment variables for Docker Compose
os.environ["HOST_BIND_IP"] = os.getenv("HOST_BIND_IP", "127.0.0.1")
os.environ["TEST_PORT"] = os.getenv("TEST_PORT", "8002")


@pytest.fixture(scope="session")
def page_url() -> str:
    """
    Returns the URL of the page to be tested.
    """
    host_bind_ip = os.getenv("HOST_BIND_IP", "127.0.0.1")
    host_port = os.getenv("TEST_PORT", "8002")
    return f"http://{host_bind_ip}:{host_port}/"


@pytest.fixture(scope="session", autouse=True)
def e2e_setup() -> Generator[None, None, None]:
    """
    Manages the lifecycle of the application for end-to-end testing.
    """
    # Determine if sudo should be used based on environment variable
    use_sudo = os.getenv("SUDO") == "true"
    docker_command = ["sudo", "docker"] if use_sudo else ["docker"]

    host_bind_ip = os.getenv("HOST_BIND_IP", "127.0.0.1")
    host_port = os.getenv("TEST_PORT", "8002")
    health_url = f"http://{host_bind_ip}:{host_port}/"

    # Define compose commands
    project_name = f"{os.getenv('PROJECT_NAME', 'dj-site-templ')}-test"
    compose_up_command = docker_command + [
        "compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.test.override.yml",
        "--project-name",
        project_name,
        "up",
        "-d",
        "--build",
    ]
    compose_down_command = docker_command + [
        "compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.test.override.yml",
        "--project-name",
        project_name,
        "down",
        "--remove-orphans",
    ]
    compose_logs_command = docker_command + [
        "compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.test.override.yml",
        "--project-name",
        project_name,
        "logs",
        "web",
        "db",
    ]

    try:
        print("\n🚀 Starting E2E services...")
        subprocess.run(
            compose_up_command, check=True, timeout=300
        )  # 5 minutes timeout

        # Health Check
        start_time = time.time()
        timeout = 300  # 5 minutes for Django application startup
        is_healthy = False
        attempt = 0
        print(f"🔍 Starting health check for Django application at {health_url}")
        while time.time() - start_time < timeout:
            attempt += 1
            elapsed = int(time.time() - start_time)
            try:
                response = httpx.get(health_url, timeout=10)
                if response.status_code == 200:
                    print(
                        f"✅ Django application is healthy! (attempt {attempt}, {elapsed}s elapsed)"
                    )
                    is_healthy = True
                    break
                else:
                    print(
                        f"⏳ Health check at {health_url} returned HTTP {response.status_code} (attempt {attempt}, {elapsed}s elapsed)"
                    )
            except httpx.RequestError as e:
                error_type = type(e).__name__
                print(
                    f"⏳ Health check at {health_url} failed: {error_type}: {e} (attempt {attempt}, {elapsed}s elapsed)"
                )
            time.sleep(5)

        if not is_healthy:
            print("Getting logs from containers...")
            subprocess.run(compose_logs_command)
            # Ensure teardown on health check failure
            print("\n🛑 Stopping E2E services due to health check failure...")
            subprocess.run(compose_down_command, check=False)
            pytest.fail(
                f"Django application did not become healthy within {timeout} seconds."
            )

        yield

    except subprocess.CalledProcessError as e:
        print("\n🛑 compose up failed; performing cleanup...")
        print(f"Exit code: {e.returncode}")
        print("Getting logs from containers...")
        subprocess.run(compose_logs_command)
        subprocess.run(compose_down_command, check=False)
        raise
    finally:
        # Stop services
        print("\n🛑 Stopping E2E services...")
        subprocess.run(compose_down_command, check=False)
