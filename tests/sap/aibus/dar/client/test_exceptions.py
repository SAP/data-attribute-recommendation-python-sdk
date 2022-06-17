import datetime
from unittest.mock import PropertyMock

from sap.aibus.dar.client.exceptions import (
    DARHTTPException,
    ModelAlreadyExists,
)
from tests.sap.aibus.dar.client.test_dar_session import create_mock_response

# TODO: test __str__

url = "http://localhost:4321/test/"

correlation_id = "412d84ae-0eb5-4421-863d-956570c2da54"
vcap_request_id = "d9cd7dec-4d74-4a7a-a953-4ca583c8d912"


def create_mock_response_404():
    mock_response = create_mock_response()

    mock_response.headers["X-Correlation-ID"] = correlation_id
    mock_response.headers["X-Vcap-Request-Id"] = vcap_request_id
    mock_response.headers["Server"] = "Gunicorn"
    mock_response.headers["X-Cf-Routererror"] = "unknown_route"
    mock_response.status_code = 404
    mock_response.request.method = "GET"
    mock_response.reason = b"\xc4\xd6\xdc Not Found"
    return mock_response


class TestDARHTTPException:
    url = "http://localhost:4321/test/"

    def test_basic(self):
        mock_response = create_mock_response_404()

        exception = DARHTTPException.create_from_response(url, mock_response)

        assert isinstance(exception, DARHTTPException)
        assert exception.response == mock_response
        assert exception.request == mock_response.request
        assert exception.status_code == 404
        assert exception.correlation_id == correlation_id
        assert exception.vcap_request_id == vcap_request_id
        assert exception.url == url
        assert exception.server_header == "Gunicorn"
        assert exception.cf_router_error == "unknown_route"
        assert isinstance(exception.exception_timestamp, datetime.datetime)
        assert exception.exception_timestamp.tzinfo == datetime.timezone.utc
        assert exception.response_reason == "ÄÖÜ Not Found"

        # Monkey-patch timestamp for deterministic testing.
        exception.exception_timestamp = datetime.datetime(
            2011, 11, 4, 0, 5, 23, 283000, tzinfo=datetime.timezone.utc
        )

        expected_debug_message = ""
        expected_debug_message += "URL: '{}'\n".format(url)
        expected_debug_message += "Method: '{}'\n".format("GET")
        expected_debug_message += "Status Code: '{}'\n".format(404)
        expected_debug_message += "Status Reason: '{}'\n".format("ÄÖÜ Not Found")
        expected_debug_message += "Response Body: '{}'\n".format(
            '{\n    "ping": "pong"\n}'
        )
        expected_debug_message += "Correlation ID: '{}'\n".format(correlation_id)
        expected_debug_message += "VCAP Request ID: '{}'\n".format(vcap_request_id)
        expected_debug_message += "CF Router Error: '{}'\n".format("unknown_route")
        expected_debug_message += "Server Header: '{}'\n".format("Gunicorn")
        expected_debug_message += "Exception Timestamp: '{}'\n".format(
            "2011-11-04T00:05:23.283000+00:00"
        )

        assert exception.debug_message == expected_debug_message

    def test_correlation_id_is_optional(self):
        mock_response = create_mock_response()
        mock_response.status_code = 403

        assert mock_response.headers.get("X-Correlation-Id", None) is None

        exception = DARHTTPException.create_from_response(url, mock_response)

        assert exception.correlation_id is None
        assert exception.status_code == 403

    def test_server_header_is_optional(self):
        mock_response = create_mock_response()
        mock_response.status_code = 500

        assert mock_response.headers.get("Server", None) is None

        exception = DARHTTPException.create_from_response(url, mock_response)

        assert exception.server_header is None
        assert exception.status_code == 500

    def test_vcap_request_id_is_optional(self):
        mock_response = create_mock_response()
        mock_response.status_code = 503

        assert mock_response.headers.get("X-Vcap-Request-Id", None) is None

        exception = DARHTTPException.create_from_response(url, mock_response)

        assert exception.vcap_request_id is None
        assert exception.status_code == 503

    def test_cf_router_error_is_optional(self):
        mock_response = create_mock_response()
        mock_response.status_code = 429

        assert mock_response.headers.get("X-Cf-Routererror", None) is None

        exception = DARHTTPException.create_from_response(url, mock_response)

        assert exception.cf_router_error is None
        assert exception.status_code == 429


class TestDARHTTPExceptionErrorBody:
    def test_response_body_is_json(self):
        mock_response = create_mock_response()
        mock_response.json.return_value = {"key": "value"}
        mock_response.text = PropertyMock(return_value="should be ignored")
        exception = DARHTTPException.create_from_response(url, mock_response)
        assert exception.response_body == '{\n    "key": "value"\n}'

    def test_response_body_is_plaintext(self):
        mock_response = create_mock_response()
        # If JSON cannot be decoded, fall back to text representation.
        mock_response.json.side_effect = ValueError
        mock_response.text = "Error occured"
        exception = DARHTTPException.create_from_response(url, mock_response)
        assert exception.response_body == "Error occured"


class TestDARHTTPExceptionReason:
    # Test handling of the reason-phrase part of the
    # status line: https://tools.ietf.org/html/rfc7230#section-3.1.2

    def test_reason_works_iso8859_1(self):
        mock_response = create_mock_response()
        # ÄÖÜ encoded as ISO-8859-1
        mock_response.reason = b"\xc4\xd6\xdc"

        exception = DARHTTPException.create_from_response(url, mock_response)

        assert exception.response_reason == "ÄÖÜ"

    def test_reason_works_utf_8(self):
        mock_response = create_mock_response()
        # ÄÖÜ encoded as UTF-8
        mock_response.reason = b"\xc3\x84\xc3\x96\xc3\x9c"

        exception = DARHTTPException.create_from_response(url, mock_response)
        assert exception.response_reason == "ÄÖÜ"

    def test_reason_works_unicode_object(self):
        mock_response = create_mock_response()
        mock_response.reason = "ÄÖÜ"

        exception = DARHTTPException.create_from_response(url, mock_response)
        assert exception.response_reason == "ÄÖÜ"


class TestModelAlreadyExists:
    def test_message(self):
        e = ModelAlreadyExists(model_name="a-name")
        expected_message = "Model 'a-name' already exists."
        expected_message += (
            "To re-use the name, please delete the model"
            " first or choose a different name."
        )
        assert str(e) == expected_message
