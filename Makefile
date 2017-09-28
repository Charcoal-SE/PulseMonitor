.PHONY: docker .docker-subtarget
docker: docker-build.log
	$(MAKE) -$(MAKEFLAGS) tag=$(shell awk 'END { print $$NF }' $<) \
		.docker-subtarget
.docker-subtarget:
	: ${tag?Please run $(MAKE) -$(MAKEFLAGS) docker}
	docker tag $(tag) tripleee/pulsemonitor:$(tag)
	docker tag $(tag) tripleee/pulsemonitor:latest
	docker push tripleee/pulsemonitor:latest

docker-build.log: Dockerfile
	docker build --no-cache . | tee $@
