import os
from unittest.mock import MagicMock, ANY, patch
from requests.models import Response
from sap.aibus.dar.client.aiapi.dar_ai_api_file_upload_client import (
    DARAIAPIFileUploadClient,
)
import json

BASE_URL = "https://dar-dummy.cfapps.sap.hana.ondemand.com/model-manager/v2/lm"
AUTH_URL = "https://dummy.authentication.sap.hana.ondemand.com/oauth/token"


class TestDARAIAPIFileUploadClient:
    base_url = BASE_URL
    token = "1234567890"
    new_schema = {
        "features": [
            {"label": "title", "type": "TEXT"},
        ],
        "labels": [
            {"label": "label1", "type": "CATEGORY"},
            {"label": "label2", "type": "CATEGORY"},
            {"label": "label3", "type": "CATEGORY"},
            {"label": "label4", "type": "CATEGORY"},
            {"label": "label5", "type": "CATEGORY"},
        ],
        "name": "arxiv-multilabel-prediction",
    }

    def get_failed_response(self, status_code, remote_path, error_message):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = status_code
        mock_response.json.return_value = {
            "code": "03021655",
            "message": error_message,
            "target": remote_path,
            "requestId": "9832bf934f3743v3948v3",
            "details": [
                {"code": "01041211", "message": "Optional nested error message."}
            ],
        }
        return mock_response

    get_mock_token = lambda self: self.token  # noqa: E731

    def test_constructor(self):
        """Test the basic constructor."""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )
        assert client.base_url == self.base_url + "/files"
        assert client.get_token == self.get_mock_token

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_delete_file(self, mock_send):
        """Test the delete file method successfully"""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 204
        mock_response.text = "File deleted successfully"
        mock_send.return_value = mock_response

        remote_path = "/local-dev/schema.json"
        response = client.delete_file(remote_path)

        assert response.status_code == 204
        assert "File deleted successfully" in response.text
        mock_send.assert_called_once_with(
            "DELETE", self.base_url + "/files" + remote_path
        )

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_delete_file_bad_request(self, mock_send):
        """Test the delete file for bad request"""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )
        remote_path = "/local-dev/schema.json"

        error_message = (
            "Bad request encountered. Please try again with possible-solution-here."
        )
        status_code = 400
        mock_send.return_value = self.get_failed_response(
            status_code, remote_path, error_message
        )
        response = client.delete_file(remote_path)

        assert response.status_code == 400
        assert response.json()["message"] == error_message
        mock_send.assert_called_once_with(
            "DELETE", self.base_url + "/files" + remote_path
        )

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_delete_file_no_resource(self, mock_send):
        """Test the delete file for no resource found"""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )
        remote_path = "/local-dev/schema.json"

        error_message = (
            "The resource you requested was not found."
            " Please try again with possible-solution-here."
        )
        status_code = 404
        mock_send.return_value = self.get_failed_response(
            status_code, remote_path, error_message
        )

        response = client.delete_file(remote_path)

        assert response.status_code == 404
        assert response.json()["message"] == error_message
        mock_send.assert_called_once_with(
            "DELETE", self.base_url + "/files" + remote_path
        )

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_put_file(self, mock_send):
        """Test the upload file successfully"""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "File uploaded successfully"
        mock_send.return_value = mock_response

        filename = "schema.json"
        with open(filename, "w") as json_file:
            json.dump(self.new_schema, json_file, indent=4)

        local_path = "schema.json"
        remote_path = "/local-dev/schema.json"
        overwrite = True

        response = client.put_file(local_path, remote_path, overwrite)

        assert response.status_code == 201
        assert "File uploaded successfully" in response.text
        mock_send.assert_called_once_with(
            method="PUT",
            url=self.base_url + "/files" + remote_path,
            headers={"Content-Type": "application/octet-stream"},
            params={"overwrite": overwrite},
            data=ANY,
        )

        os.remove(local_path)

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_put_file_bad_request(self, mock_send):
        """Test the upload file with a bad request"""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        filename = "schema.json"
        with open(filename, "w") as json_file:
            json.dump(self.new_schema, json_file, indent=4)

        local_path = "schema.json"
        remote_path = "/local-dev/schema.json"
        overwrite = True

        error_message = (
            "Bad request encountered. " "Please try again with possible-solution-here."
        )
        status_code = 400
        mock_send.return_value = self.get_failed_response(
            status_code, remote_path, error_message
        )
        response = client.put_file(local_path, remote_path, overwrite)

        assert response.status_code == 400
        assert response.json()["message"] == error_message
        mock_send.assert_called_once_with(
            method="PUT",
            url=self.base_url + "/files" + remote_path,
            headers={"Content-Type": "application/octet-stream"},
            params={"overwrite": overwrite},
            data=ANY,
        )

        os.remove(local_path)

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_put_file_already_exists(self, mock_send):
        """Test the upload file when file already exists"""
        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        filename = "schema.json"
        with open(filename, "w") as json_file:
            json.dump(self.new_schema, json_file, indent=4)

        local_path = "schema.json"
        remote_path = "/local-dev/schema.json"
        overwrite = True

        error_message = (
            "The specified file already exists and cannot be overwritten. "
            "Please try again with possible-solution-here."
        )
        status_code = 409
        mock_send.return_value = self.get_failed_response(
            status_code, remote_path, error_message
        )
        response = client.put_file(local_path, remote_path, overwrite)

        assert response.status_code == 409
        assert response.json()["message"] == error_message
        mock_send.assert_called_once_with(
            method="PUT",
            url=self.base_url + "/files" + remote_path,
            headers={"Content-Type": "application/octet-stream"},
            params={"overwrite": overwrite},
            data=ANY,
        )

        os.remove(local_path)

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_put_file_exceeds_limit(self, mock_send):
        """Test the upload file with a file that exceeds limit"""

        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        filename = "schema.json"
        with open(filename, "w") as json_file:
            json.dump(self.new_schema, json_file, indent=4)

        local_path = "schema.json"
        remote_path = "/local-dev/schema.json"
        overwrite = True

        error_message = "The file size exceeds the supported limit."
        status_code = 413
        mock_send.return_value = self.get_failed_response(
            status_code, remote_path, error_message
        )

        response = client.put_file(local_path, remote_path, overwrite)

        assert response.status_code == 413
        assert (
            response.json()["message"] == "The file size exceeds the supported limit."
        )
        mock_send.assert_called_once_with(
            method="PUT",
            url=self.base_url + "/files" + remote_path,
            headers={"Content-Type": "application/octet-stream"},
            params={"overwrite": overwrite},
            data=ANY,
        )

        os.remove(local_path)

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_get_file_from_url(self, mock_send):
        """Test downloading a file using url successfully"""

        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = "File content here"
        mock_send.return_value = mock_response

        url = self.base_url + "/files/local-dev/arxiv.csv.gz"
        response = client.get_file_from_url(url)

        assert response.status_code == 200
        assert "File content here" in response.text
        mock_send.assert_called_once_with("GET", url)

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_get_file_from_url_bad_request(self, mock_send):
        """Test downloading a file using url with a bad request"""

        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        url = self.base_url + "/files/local-dev/arxiv.csv.gz"
        error_message = (
            "Bad request encountered. Please try again with possible-solution-here."
        )
        status_code = 400
        mock_send.return_value = self.get_failed_response(
            status_code, url, error_message
        )
        response = client.get_file_from_url(url)

        assert response.status_code == 400
        assert (
            response.json()["message"]
            == "Bad request encountered. Please try again with possible-solution-here."
        )
        mock_send.assert_called_once_with("GET", url)

    @patch.object(DARAIAPIFileUploadClient, "_send")
    def test_get_file_from_url_not_found(self, mock_send):
        """Test downloading a file using url when file not found"""

        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )

        url = self.base_url + "/files/local-dev/arxiv.csv.gz"
        error_message = (
            "The resource you requested was not found."
            "Please try again with possible-solution-here."
        )
        status_code = 404
        mock_send.return_value = self.get_failed_response(
            status_code, url, error_message
        )
        response = client.get_file_from_url(url)

        assert response.status_code == 404
        assert (
            response.json()["message"]
            == "The resource you requested was not found.Please try again with "
            "possible-solution-here."
        )
        mock_send.assert_called_once_with("GET", url)

    @patch("requests.Session.send")
    def test_send_get_request_success(self, mock_send):
        """Test _send method with a successful GET request."""

        client = DARAIAPIFileUploadClient(
            base_url=self.base_url, get_token=self.get_mock_token
        )
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_response.json.return_value = {"message": "Success"}
        mock_send.return_value = mock_response

        url = self.base_url + "/files/local-dev/arxiv.csv.gz"
        response = client._send("GET", url)

        assert response.status_code == 200
        assert response.json() == {"message": "Success"}

        mock_send.assert_called_once()
