SHELL := /bin/bash
.PHONY: aws clean importer_config import

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
	@ENV_PATH="./../logs_importer/.env"; \
	OS=$$(uname -s); \
	cd aws && \
	export TF_TRAIL_BUCKET=$$(terraform output -raw cloud_trail_bucket_name) && \
	export TF_TRAIL_BUCKET_REGION=$$(terraform output -raw cloud_trail_bucket_region) && \
	{ test -n "$$TF_TRAIL_BUCKET" || { echo "TF_TRAIL_BUCKET is empty." && exit 1; }; } && \
	echo "Bucket: $$TF_TRAIL_BUCKET" && \
	echo "Bucket Region: $$TF_TRAIL_BUCKET_REGION" && \
	if [ "$$OS" = "Linux" ]; then \
		sed -i '/LOGS_BUCKET=/d' $$ENV_PATH; \
		sed -i '/AWS_REGION=/d' $$ENV_PATH; \
	elif [ "$$OS" = "Darwin" ]; then \
		sed -i '' '/LOGS_BUCKET=/d' $$ENV_PATH; \
		sed -i '' '/AWS_REGION=/d' $$ENV_PATH; \
	fi && \
	echo "LOGS_BUCKET=$$TF_TRAIL_BUCKET" >> $$ENV_PATH && \
	echo "AWS_REGION=$$TF_TRAIL_BUCKET_REGION" >> $$ENV_PATH

import:
	python -m logs_importer.main


