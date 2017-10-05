.PHONY: build docker-push
build: docker-build.log
docker-push: docker-build.log
	docker push tripleee/pulsemonitor:latest

docker-build.log: Dockerfile run
	docker build --no-cache -t tripleee/pulsemonitor:latest . | tee $@

.PHONY: clean realclean distclean
clean:
	:
realclean: clean
	-image=$$(awk 'END { print $$NF }' docker-build.log) \
	&& docker ps -q -f ancestor=$$image \
	| xargs -r docker kill \
	&& docker rmi $$image
	$(RM) docker-build.log
distclean: realclean
	:
