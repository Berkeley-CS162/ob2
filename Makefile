up:
	docker build -t cs162/ob2:latest -f build/Dockerfile .
	docker-compose -f build/docker-compose.yaml up

down:
	docker-compose -f build/docker-compose.yaml down