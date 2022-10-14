from pathlib import Path


def test_dataset_class():
    from policyengine_core.data.dataset import Dataset
    from policyengine_core.periods import period

    tmp_folder_path = Path(__file__).parent / "tmp"
    tmp_folder_path.mkdir(exist_ok=True)

    class TestDataset(Dataset):
        name = "test_dataset"
        label = "Test dataset"
        folder_path = tmp_folder_path
        data_format = Dataset.TIME_PERIOD_ARRAYS

        def generate(self, year: int) -> None:
            input_period = period("2022-01")
            self.save_variable_values(
                year, {"salary": {input_period: [100, 200, 300]}}
            )

    TestDataset = TestDataset()

    test_dataset = TestDataset
    test_dataset.remove_all()
    test_dataset.generate(2022)
    saved_datasets = test_dataset.years
    assert len(saved_datasets) == 1
    assert saved_datasets[0] == 2022
    test_dataset.remove(2022)
    assert len(test_dataset.years) == 0
