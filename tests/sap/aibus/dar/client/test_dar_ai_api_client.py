from sap.aibus.dar.client.aiapi.dar_ai_api_client import DARAIAPIClient
import unittest

from sap.aibus.dar.client.aiapi.dar_ai_api_file_upload_client import (
    DARAIAPIFileUploadClient,
)

BASE_URL = "https://dar-dummy.cfapps.sap.hana.ondemand.com/model-manager/v2/lm"
AUTH_URL = "https://dummy.authentication.sap.hana.ondemand.com/oauth/token"


class TestDARAIAPIClient(unittest.TestCase):
    base_url = BASE_URL
    auth_url = AUTH_URL
    client_id = "a-client-id"
    client_secret = "a-client-secret"
    token = "1234567890"

    def test_constructor(self):
        """Test the basic constructor."""
        client = DARAIAPIClient(
            base_url=self.base_url,
            auth_url=self.auth_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        assert client.base_url == self.base_url
        assert isinstance(client.file_upload_client, DARAIAPIFileUploadClient)
