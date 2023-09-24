SHELL := /bin/bash
.PHONY: aws clean

aws:
	cd aws; \
	terraform init; \
	terraform apply -auto-approve
	cd .docker \
	docker compose up -d

clean:
	cd aws; \
	terraform destroy -auto-approve
	cd ./docker; \
    docker compose down


