.PHONY: up down logs test seed reset

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f app

test:
	docker compose run --rm app pytest -q

seed:
	docker compose exec app python -m scripts.seed_demo_data

reset:
	docker compose exec app python -m scripts.reset_db
