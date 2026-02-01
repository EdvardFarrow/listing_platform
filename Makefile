.PHONY: help up up-build down restart clean ps logs init

help: ## Показать список доступных команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'


init:
	@echo "Initializing project..."
	docker compose up --build -d
	@echo "✅ Database is healthy. Applying migrations..."
	docker compose exec web python manage.py migrate
	@echo "✅ Project is ready! Docs: http://127.0.0.1:8000/api/docs"

up: ## Запустить проект
	docker compose up -d

up-build: ## Пересобрать и запустить проект
	docker compose up --build -d

down: ## Остановить контейнеры
	docker compose down

restart: down up ## Перезапустить проект

clean: ## Остановить проект и удалить данные (сброс БД)
	docker compose down -v
	@echo "⚠️  База данных и кэш очищены!"

migrate: ## Применить миграции
	docker compose exec web python manage.py migrate

ps: ## Показать статус контейнеров
	docker compose ps

logs: ## Смотреть логи всех сервисов
	docker compose logs -f
