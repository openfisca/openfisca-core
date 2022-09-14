from . import distribution


def test_package_name_header(test_client):
    parameters_response = test_client.get("/parameters")
    assert parameters_response.headers.get("Country-Package") == distribution.key


def test_package_version_header(test_client):
    parameters_response = test_client.get("/parameters")
    assert parameters_response.headers.get("Country-Package-Version") == distribution.version
