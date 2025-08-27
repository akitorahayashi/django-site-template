# --- Base Stage ---
# Defines the base image for subsequent stages
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir --disable-pip-version-check poetry \
    && poetry config virtualenvs.in-project true

# --- Builder Stage ---
# Installs all dependencies (for development and production)
FROM base as builder

# Copy only the files necessary for installing dependencies
COPY poetry.lock pyproject.toml ./

# Install all dependencies, including dev dependencies
RUN poetry install --no-root


# --- Prod-Builder Stage ---
# Installs only production dependencies
FROM base as prod-builder

# Copy only the files necessary for installing dependencies
COPY poetry.lock pyproject.toml ./

# Install only production dependencies
RUN poetry install --no-root --only main


# --- Production Stage ---
# Final image for production (without Poetry)
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Create a non-privileged user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

# Copy virtual environment from the prod-builder stage
COPY --from=prod-builder /app/.venv/ /opt/venv/
# Ensure venv on PATH
ENV PATH="/opt/venv/bin:${PATH}"
# Copy the entrypoint script
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy application code with correct permissions
COPY --chown=appuser:appgroup manage.py .
COPY --chown=appuser:appgroup apps/ ./apps/
COPY --chown=appuser:appgroup config/ ./config/

# Grant ownership of the app directory to the appuser
# This allows the user to create files like the SQLite database
RUN chown appuser:appgroup /app

# Switch to the non-privileged user
USER appuser

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
