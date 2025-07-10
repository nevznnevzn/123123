# Multi-stage build для уменьшения размера образа
FROM python:3.11-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Финальный образ
FROM python:3.11-slim

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем установленные зависимости
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY . .

# Устанавливаем права доступа
RUN chown -R app:app /app
USER app

# Создаем директории для логов и данных
RUN mkdir -p logs assets

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import asyncio; asyncio.run(__import__('database_async').async_db_manager.get_total_users_count())" || exit 1

# Порт для мониторинга (если будет webhook)
EXPOSE 8080

# Запуск приложения
CMD ["python", "main_simple.py"] 