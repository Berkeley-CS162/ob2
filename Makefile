up:
	docker build -t cs162/ob2:latest -f build/Dockerfile .
	docker-compose -f build/docker-compose.yaml up

down:
	docker-compose -f build/docker-compose.yaml down

apparmor:
	sudo cp build/etc.apparmor.d.ob2docker /etc/apparmor.d/ob2docker
	sudo apparmor_parser -r -T -W /etc/apparmor.d/ob2docker