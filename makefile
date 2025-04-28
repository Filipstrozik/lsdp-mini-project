stage_1_up:
	docker compose -f docker-compose.yml start
stage_1_down:
	docker compose -f docker-compose.yml stop

stage_2_up:
	docker compose -f docker-compose-redash.yml start

stage_2_down:
	docker compose -f docker-compose-redash.yml stop

stage_3_up:
	docker compose -f docker-compose-spark.yml start

stage_3_down:
	docker compose -f docker-compose-spark.yml stop