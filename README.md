# Django Project Template

This is a comprehensive Django project template designed to be a starting point for various web applications. It comes with modern development practices, including Docker, Makefile, and a CI/CD pipeline using GitHub Actions.

## ✅ Prerequisites

Before you begin, ensure you have the following tools installed:

- **Docker**: Latest version recommended
- **Docker Compose**: Included with Docker
- **Make**: The `make` command should be available
- **Python**: 3.12 (recommended, see `.python-version`)
- **Poetry**: 1.8.3 or compatible (for local development)

## 🚀 Getting Started

To start your new project, clone this repository. Then, to set up the local environment, install dependencies, and create a default `.env` file, simply run:

```bash
make setup
```

This command installs all necessary packages with Poetry and creates a `.env` file from the `.env.example` template if it doesn't already exist. You can customize the `.env` file with your specific production settings.

    For more details, see the **Environment Variable Management** section below.

## ⚙️ Environment Variable Management

This project uses a layered approach to manage environment variables, allowing for flexible configuration across different environments.

-   **.env**: The base configuration file. It should contain all necessary variables for the **production** environment. It is not committed to Git.
-   **.env.development**: Contains overrides for the **development** environment (e.g., `DEBUG=True`). It is committed to Git.
-   **.env.test**: Contains overrides for the **testing** environment (e.g., in-memory database). It is committed to Git.
-   **.env.local**: For personal, local overrides. This file is **not** committed to Git and can be used to temporarily change settings without affecting other environments.

The configuration is loaded with the following priority: `.env.local` > `.env.{DJANGO_ENV}` > `.env`. The `DJANGO_ENV` variable is automatically set by the `Makefile` commands (e.g., `development` for `make up`, `test` for `make test`).

## 🐳 Building and Running with Docker

The application is designed to run inside Docker containers.

### Development

To build and start the development containers in the background, use:
```bash
make up
```
This command sets `DJANGO_ENV=development`, so settings from `.env.development` are automatically applied. The application will be accessible at `http://localhost:8000`.

To stop and remove the containers, run:
```bash
make down
```

### Production

To run the application in a production-like environment, use:
```bash
make up-prod
```
This command sets `DJANGO_ENV=production`, which uses the base `.env` file for configuration. Ensure your `.env` file is correctly configured for production before running this command.

To stop and remove the production-like containers:
```bash
make down-prod
```

## ✅ Testing and Code Quality

The project is equipped with tools to maintain code quality, including tests, a linter, and a formatter.

### Running Tests

To run the full test suite, use the following command:
```bash
make test
```
This command sets `DJANGO_ENV=test` to ensure the test-specific configuration from `.env.test` is used.

### Code Formatting and Linting

We use `black` and `ruff` to automatically format the code.

To format your code:
```bash
make format
```

To check for linting and formatting issues (as the CI pipeline does):
```bash
make lint
```

## 📂 Project Structure

A key feature of this template is how Django apps are organized.

-   **`apps/` directory**: All Django applications reside within the `apps/` directory.
-   **Namespace Package**: The `apps/` directory is configured as a [PEP 420 namespace package](https://www.python.org/dev/peps/pep-0420/), meaning it does **not** contain an `__init__.py` file. This allows for better separation of concerns and makes it easier to add or remove apps.
-   **Packaging**: The `pyproject.toml` file is configured to include the entire `apps` directory in the distribution.

## 🛠 Makefile Commands

A list of all available commands can be viewed by running `make help`. Here is an overview of the main commands:

| Command              | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| `make setup`          | Installs project dependencies using Poetry.                                 |
| `make up`             | Builds and starts the development Docker containers (`DJANGO_ENV=development`). |
| `make down`           | Stops and removes the development Docker containers.                        |
| `make rebuild`        | Rebuilds development containers without cache and restarts them.            |
| `make logs`           | Shows the logs for the development containers.                              |
| `make shell`          | Opens a shell inside the `web` container for development.                   |
| `make up-prod`        | Builds and starts the production-like Docker containers (`DJANGO_ENV=production`). |
| `make down-prod`      | Stops and removes the production-like Docker containers.                    |
| `make migrate`        | Runs database migrations in the development environment.                    |
| `make makemigrations` | Creates new migration files based on model changes.                         |
| `make superuser`      | Creates a Django superuser in the development environment.                  |
| `make migrate-prod`   | Runs database migrations in the production environment.                     |
| `make superuser-prod` | Creates a Django superuser in the production environment.                   |
| `make test`           | Runs the test suite with `DJANGO_ENV=test`.                                 |
| `make format`         | Formats the code using `black` and `ruff`.                                  |
| `make lint`           | Checks for linting and formatting errors.                                   |
| `make clean`          | Stops all containers and cleans up generated files.                         |
| `make help`           | Displays a list of all available commands and their descriptions.           |
