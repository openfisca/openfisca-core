import warnings

from openfisca_core.warnings import MemoryConfigWarning


class MemoryConfig:
    def __init__(
        self,
        max_memory_occupation,
        priority_variables=None,
        variables_to_drop=None,
    ) -> None:
        message = [
            "Memory configuration is a feature that is still currently under experimentation.",
            "You are very welcome to use it and send us precious feedback,",
            "but keep in mind that the way it is used might change without any major version bump.",
        ]
        warnings.warn(" ".join(message), MemoryConfigWarning, stacklevel=2)

        self.max_memory_occupation = float(max_memory_occupation)
        if self.max_memory_occupation > 1:
            msg = "max_memory_occupation must be <= 1"
            raise ValueError(msg)
        self.max_memory_occupation_pc = self.max_memory_occupation * 100
        self.priority_variables = (
            set(priority_variables) if priority_variables else set()
        )
        self.variables_to_drop = set(variables_to_drop) if variables_to_drop else set()
