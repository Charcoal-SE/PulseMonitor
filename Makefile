.PHONY: docker-push
docker-push: docker-build.log
	docker push tripleee/pulsemonitor:latest

docker-build.log: Dockerfile run
	docker build --no-cache -t tripleee/pulsemonitor:latest . | tee $@
