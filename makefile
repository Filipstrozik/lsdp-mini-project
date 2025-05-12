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


create_cluster:
	k3d cluster create PolWro \
	--agents 1 \
	--volume /Users/filipstrozik/Documents/studies/IIISEM/lsdp-mini-project/k3d/data:/Users/filipstrozik/Documents/studies/IIISEM/lsdp-mini-project/k3d/data@all

start_cluster:
	k3d cluster start PolWro

stop_cluster:
	k3d cluster stop PolWro

delete_cluster:
	k3d cluster delete PolWro

helm_setup:
	bash -c 'mkdir -p ./k3d/data/{redis,rabbitmq,mongodb,postgres,prometheus,grafana,flower,hf_cache,data,models}'
	# cp ./models/vit_model_scripted.pt ./k3d/data/models/vit_model_scripted.pt
	chmod -R 775 ./k3d/data
	helm dependency update ./helm/polwro
	helm template ./helm/polwro  --skip-tests | kubectl apply -f - --dry-run=server

helm_install:
	helm install polwro ./helm/polwro -f ./helm/polwro/values.yaml

helm_upgrade:
	helm upgrade polwro ./helm/polwro -f ./helm/polwro/values.yaml

helm_rollback:
	helm rollback polwro 1

helm_uninstall:
	helm uninstall polwro

make port:
	kubectl port-forward service/frontend-service 4200:80 &
	kubectl port-forward service/graphql-service  5000:5000 &
	kubectl port-forward service/grpc-service 50051:50051 &
