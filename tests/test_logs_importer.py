import gzip
import json
from unittest.mock import MagicMock

import pytest

from logs_importer.main import LogsImporter


@pytest.fixture
def mock_boto3_client(mocker):
    return mocker.patch("logs_importer.main.boto3.client", autospec=True)


@pytest.fixture
def mock_mongo_client(mocker):
    return mocker.patch("logs_importer.main.pymongo.MongoClient", autospec=True)


@pytest.fixture
def logs_importer(mock_boto3_client, mock_mongo_client):
    test_config = {
        "aws_region": "us-west-2",
        "logs_bucket": "my-mock-bucket",
        "logs_path": "some/path/",
        "remove_imported_s3_files": True,
        "mongo_collection_logs": "logs",
        "mongo_collection_metadata": "metadata",
        "mongo_db": "mock_db",
        "mongo_host": "localhost:27017",
        "mongo_password": "password",
        "mongo_user": "user",
    }

    return LogsImporter(config=test_config)


def test_fetch_logs_list(logs_importer):
    mock_response = {
        "Contents": [
            {"Key": "path/to/log1"},
            {"Key": "path/to/log2"},
        ]
    }
    logs_importer.s3_client.list_objects_v2.return_value = mock_response

    result = logs_importer.fetch_logs_list()
    assert result == ["path/to/log1", "path/to/log2"]


def test_s3_needs_import(logs_importer):
    mock_mongo_result = MagicMock()
    mock_mongo_result.upserted_id = None
    mock_mongo_result.modified_count = 1
    logs_importer.metadata_collection.update_one.return_value = mock_mongo_result

    s3_obj = {"ContentLength": 123}
    key = "path/to/log1"

    result = logs_importer.s3_needs_import(s3_obj, key)
    assert result is True


def test_import_logs(logs_importer):
    logs_importer.fetch_logs_list = MagicMock(return_value=["path/to/log1"])

    test_log_content = json.dumps({"Records": [{"eventID": "1"}, {"eventID": "2"}]})
    compressed_content = gzip.compress(bytes(test_log_content, "utf-8"))

    mock_s3_obj = {"Body": MagicMock(read=MagicMock(return_value=compressed_content))}
    logs_importer.s3_client.get_object.return_value = mock_s3_obj
    logs_importer.s3_needs_import = MagicMock(return_value=True)
    logs_importer.logs_collection.replace_one = MagicMock()

    logs_importer.import_logs()
    logs_importer.logs_collection.replace_one.assert_called()
