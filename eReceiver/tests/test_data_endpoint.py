import logging
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from main import APP_ROUTES, app

client = TestClient(app)


class TestDataEndpoint:
    @pytest.fixture
    def task_valid_payload(self):
        return {
            "status": "ComPlETe",
            "type": 11,
            "hash": "661f8009fa8e56a9d0e94a0a644397d7",
        }

    @pytest.fixture
    def task_invalid_status(self):
        return {
            "status": "<invalid status>",
            "type": 11,
            "hash": "661f8009fa8e56a9d0e94a0a644397d7",
        }

    def task_invalid_type(self):
        return {
            "status": "complete",
            "type": 12,
            "hash": "661f8009fa8e56a9d0e94a0a644397d7",
        }

    def task_invalid_hash(self):
        return {
            "status": "complete",
            "type": 11,
            "hash": "661f8009fa8e56a9d0e94a0a644397dz",
        }

    def test_data_endpoint_will_accept_only_POST_requests_with_payload(
        self, task_valid_payload
    ):
        response = client.post(APP_ROUTES.get("data"), json=task_valid_payload)
        assert response.status_code == HTTPStatus.OK

    def test_data_endpoint_invalid_task_status_fails_validation(
        self, task_invalid_status
    ):
        response = client.post(APP_ROUTES.get("data"), json=task_invalid_status)

        response_detail = response.json()["detail"][0]
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_detail["loc"] == ["body", "status"]
        assert response_detail["type"] == "assertion_error"

    def test_data_endpoint_empty_payload_fails_validation(self):
        response = client.post(APP_ROUTES.get("data"), json={})

        response_detail = response.json()["detail"][0]
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_detail["type"] == "missing"

    def test_data_endpoint_invalid_task_type_fails_validation(
        self,
    ):

        task_invalid_type = self.task_invalid_type()
        for task_type in range(13):
            # hard code, see caveats
            if task_type in [1, 2, 5, 11]:
                continue

            task_invalid_type["type"] = task_type
            response = client.post(APP_ROUTES.get("data"), json=task_invalid_type)
            response_detail = response.json()["detail"][0]

            assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
            assert response_detail["loc"] == ["body", "type"]
            assert response_detail["type"] == "assertion_error"

    @pytest.mark.parametrize(
        "invalid_hash",
        [
            12345,  # fails to validate as str also
            "wewqewqeqewqewqeqwe",
            "661f8009fa8e56a9d0e94a0a644397",  # 30 chars
            "661f8009fa8e56a9d0e94a0a644397wwwwwwwwww",  # >32 chars
            "661f8009fa8e56a9d0e94a0a644397dz",  # invalid char 'z'
        ],
    )
    def test_data_endpoint_invalid_task_hash_fails_validation(self, invalid_hash):

        task_invalid_hash = self.task_invalid_hash()
        task_invalid_hash["hash"] = invalid_hash

        response = client.post(APP_ROUTES.get("data"), json=task_invalid_hash)

        response_detail = response.json()["detail"][0]
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_detail["loc"] == ["body", "hash"]

        if isinstance(invalid_hash, str):
            assert response_detail["type"] == "assertion_error"
        else:
            assert response_detail["type"] == "string_type"

    def test_data_endpoint_logs_exception_with_log_error_if_request_not_valid(
        self, caplog, task_invalid_status
    ):
        with caplog.at_level(logging.INFO):
            client.post(APP_ROUTES.get("data"), json=task_invalid_status)

            for record in caplog.records:
                if record.levelno != logging.ERROR:
                    continue

                assert "Input data is not valid:" in record.msg
                assert str(task_invalid_status) in record.msg
