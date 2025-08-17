all: lint clean build test

build:
	docker compose build

changelog:
	docker run --quiet --rm --volume "${PWD}:/mnt/source" --workdir /mnt/source ghcr.io/cbdq-io/gitchangelog > CHANGELOG.md

clean:
	docker compose down -t 0

lint:
	helm lint charts/smtp2s3
	docker run --rm -i hadolint/hadolint < Dockerfile
	yamllint -s .
	isort -v .
	flake8

requirements:
	python -m pip install --upgrade pip
	pip install -Ur requirements-dev.txt -r requirements.txt
	pip check

tag:
	@python -c 'import smtp2s3; print(smtp2s3.__version__);'

test:
	docker compose up -d --wait
	docker compose exec minio mc alias set myminio http://minio:9000 minioadminid minioadminsec
	docker compose exec minio mc mb myminio/mybucket
	PYTHONPATH=. pytest -v tests
