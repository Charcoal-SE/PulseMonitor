.PHONY: build docker-push tests
build: docker-build.log
docker-push: docker-build.log
	docker push tripleee/pulsemonitor:latest

docker-build.log: Dockerfile run.prod redunda_key.txt location.txt \
		room_65945_name_Charcoal_Test_privileged_users \
		Source/*.py requirements.txt
	-awk '/^Successfully built/ { i=$$NF } END { if (i) print i }' $@ \
	| xargs docker rmi
	docker build --no-cache -t tripleee/pulsemonitor:latest . | tee $@

run.prod:
	@echo Copy the file run and update it with your bot\'s credentials >&2
	exit 222

.PHONY: clean realclean distclean
clean:
	:
realclean: clean
	$(RM) -rf venv .coverage .pytest_cache
	-image=$$(awk 'END { print $$NF }' docker-build.log) \
	&& docker ps -q -f ancestor=$$image \
	| xargs -r docker kill \
	&& docker rmi $$image
	$(RM) docker-build.log
distclean: realclean
	:

venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install pytest pytest-cov

tests: venv
	venv/bin/pytest
