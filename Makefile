.PHONY: help install install-dev test test-cov lint format check clean run

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости для продакшена
	uv pip install -e .

install-dev: ## Установить зависимости для разработки
	uv pip install -e ".[dev]"
	pre-commit install

test: ## Запустить тесты
	python -m pytest tests/ -v

test-cov: ## Запустить тесты с покрытием
	python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

lint: ## Проверить качество кода
	flake8 .
	mypy .

format: ## Отформатировать код
	black .
	isort .

check: ## Полная проверка кода
	black --check .
	isort --check-only .
	flake8 .
	mypy .

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

run: ## Запустить бота
	python main.py

.DEFAULT_GOAL := help 