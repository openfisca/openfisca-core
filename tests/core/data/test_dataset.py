def test_dataset_class():
    from policyengine_core.data.dataset import Dataset
    from policyengine_core.periods import period

    class TestDataset(Dataset):
        name = "test_dataset"
        label = "Test dataset"
        options = {"year": 2022}
        country_package_name: str = "policyengine_core.country_template"

        def build(self, options: dict = None) -> None:
            input_period = period("2022-01")
            self.write({"salary": {input_period: [100, 200, 300]}})

    test_dataset = TestDataset()
    test_dataset.remove_all()
    test_dataset.build()
    saved_datasets = test_dataset.get_saved_datasets()
    assert len(saved_datasets) == 1
    assert saved_datasets[0]["year"] == "2022"
    test_dataset.remove({"year": "2022"})
    assert len(test_dataset.get_saved_datasets()) == 0
