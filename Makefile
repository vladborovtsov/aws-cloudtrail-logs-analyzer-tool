SHELL := /bin/bash
.PHONY: aws clean importer_config

aws:
	@cd aws; \
	terraform init; \
	terraform apply -auto-approve
	cd ./docker; \
	docker compose up -d

clean:
	cd aws; \
	terraform destroy -auto-approve
	cd ./docker; \
	docker compose down

importer_config:
	@cd aws && \
	export TF_TRAIL_BUCKET=$$(terraform output -raw cloud_trail_bucket_name) && \
	export TF_TRAIL_BUCKET_REGION=$$(terraform output -raw cloud_trail_bucket_region) && \
	{ test -n "$$TF_TRAIL_BUCKET" || { echo "TF_TRAIL_BUCKET is empty." && exit 1; }; } && \
	echo "Bucket: $$TF_TRAIL_BUCKET" && \
	echo "Bucket Region: $$TF_TRAIL_BUCKET_REGION"

