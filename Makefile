# latest = latest
version=latest
docker-user=jaredhanson11
name=${docker-user}/flok-admin

build-images:
	docker build . --build-arg PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} -t ${name}:${version}
push-images: build
	docker push ${name}:${version}
