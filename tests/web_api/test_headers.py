def test_package_name_header(test_client, distribution):
    name = distribution.metadata.get("Name").lower()
    parameters_response = test_client.get("/parameters")
    assert parameters_response.headers.get("Country-Package") == name


def test_package_version_header(test_client, distribution):
    version = distribution.metadata.get("Version")
    parameters_response = test_client.get("/parameters")
    assert parameters_response.headers.get("Country-Package-Version") == version
