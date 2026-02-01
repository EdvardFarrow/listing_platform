.PHONY: help up up-build down restart clean logs logs-bot logs-web ps db redis test


help: ## Показать список доступных команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

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


ps: ## Показать статус контейнеров
	docker compose ps

logs: ## Смотреть логи всех сервисов
	docker compose logs -f

logs-bot: ## Смотреть логи только бота
	docker compose logs -f bot

logs-web: ## Смотреть логи только веб-интерфейса
	docker compose logs -f web