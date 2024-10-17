import os
from typing import List

from _pytest.nodes import Item
from py.xml import html
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


# Traceability report generation
# The following hooks implement the traceability report generation.
# This roughly works as follows:
#
# * In the runtest_setup hook, the issue ID is extracted from the closest
#   `requirement` marker and stored on the test `item` object
# * In the runtest_makereport hook, the issue ID is copied from the test `item`
#   to the report object (basically, to the test result)
# * Finally, the issue ID is consumed in the pytest_html_results_table_header and
#   pytest_html_results_table_row hooks (provided by pytest-html plugin)
#   and added to the HTML report


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requirements(issues=[issue1, ...]): link to GitHub issue (traceability)",
    )


def pytest_runtest_setup(item: Item):
    collected_issue_ids = []  # type: List[str]
    for requirement_marker in item.iter_markers("requirements"):
        if requirement_marker and "issues" in requirement_marker.kwargs:
            collected_issue_ids.extend(requirement_marker.kwargs.get("issues", []))
    # Only keep unique IDs and sort them
    item.issue_ids = sorted(set(collected_issue_ids))  # type:ignore


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call):
    outcome = yield

    report = outcome.get_result()

    if hasattr(item, "issue_ids"):
        report.issue_ids = item.issue_ids  # type:ignore


def pytest_html_results_table_header(cells):
    # remove "links" column
    cells.pop()
    cells.insert(
        0, html.th("Requirement", class_="sortable requirement", col="requirement")
    )


def pytest_html_results_table_row(report, cells):
    base_url = "https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/"

    # remove "links" column
    cells.pop()
    issue_ids = getattr(report, "issue_ids", None)

    if issue_ids:
        links = []
        for issue_id in issue_ids:
            url = base_url + issue_id
            # There must be a plain-text node inside the `td`, or the table sorting
            # will break. This is why the `a` element is added separately.
            links.append(f"SAP/data-attribute-recommendation-python-sdk#{issue_id} ")
            links.append(html.a("Link", href=url))
            links.append(html.br())
        # remove last <br>
        links.pop()
        cell = html.td(*links, class_="col-requirement")
    else:
        cell = html.td("N/A", class_="col-requirement")

    cells.insert(0, cell)
