from policyengine_core.data import Dataset
from policyengine_core.periods import ETERNITY, MONTH, period


class CountryTemplateDataset(Dataset):
    name = "country_template_dataset"
    label = "Country template dataset"
    options = {"year": 2022}
    country_package_name: str = "policyengine_core.country_template"

    def build(self, options: dict = None) -> None:
        person_id = [0, 1, 2]
        household_id = [0, 1]
        person_household_id = [0, 0, 1]
        person_household_role = ["parent", "child", "parent"]
        salary = [100, 0, 200]
        salary_time_period = period("2022-01")
        weight = [1e6, 1.2e6]
        weight_time_period = period("2022")
        data = {
            "person_id": {ETERNITY: person_id},
            "household_id": {ETERNITY: household_id},
            "person_household_id": {ETERNITY: person_household_id},
            "person_household_role": {ETERNITY: person_household_role},
            "salary": {salary_time_period: salary},
            "household_weight": {weight_time_period: weight},
        }
        self.write(data)
