import os

import pytest

from sap.aibus.dar.client.data_manager_client import DataManagerClient
from sap.aibus.dar.client.inference_client import InferenceClient
from sap.aibus.dar.client.model_manager_client import ModelManagerClient
from sap.aibus.dar.client.util.credentials import OnlineCredentialsSource
from sap.aibus.dar.client.workflow.model import ModelCreator


@pytest.fixture()
def dar_url():
    return os.environ["DAR_URL"]


@pytest.fixture()
def dar_client_id():
    return os.environ["DAR_CLIENT_ID"]


@pytest.fixture()
def dar_client_secret():
    return os.environ["DAR_CLIENT_SECRET"]


@pytest.fixture()
def dar_uaa_url():
    return os.environ["DAR_AUTH_URL"]


# For the following fixtures, the parameters to the functions
# will be provided by existing fixtures of the same name!


@pytest.fixture()
def credentials_source(dar_client_id, dar_client_secret, dar_uaa_url):
    return OnlineCredentialsSource(dar_uaa_url, dar_client_id, dar_client_secret)


@pytest.fixture()
def data_manager_client(dar_url, credentials_source):
    client = DataManagerClient(dar_url, credentials_source)
    return client


@pytest.fixture()
def model_manager_client(dar_url, credentials_source):
    client = ModelManagerClient(dar_url, credentials_source)
    return client


@pytest.fixture()
def inference_client(dar_url, credentials_source):
    client = InferenceClient(dar_url, credentials_source)
    return client


@pytest.fixture()
def model_creator(dar_url, credentials_source):
    create_model = ModelCreator(dar_url, credentials_source)
    return create_model
