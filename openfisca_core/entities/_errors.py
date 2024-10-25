from . import types as t


class TaxBenefitSystemUnsetError(ValueError):
    """Raised when a tax and benefit system is not set yet."""

    def __init__(self) -> None:
        msg = (
            "The tax and benefit system is not set yet. You need to set it "
            "before using this method: `entity.tax_benefit_system = ...`."
        )
        super().__init__(msg)


class VariableNotFoundError(IndexError):
    """Raised when a requested variable is not defined for as entity."""

    def __init__(self, name: t.VariableName, plural: t.EntityPlural) -> None:
        msg = (
            f"You requested the variable '{name}', but it was not found in "
            f"the entity '{plural}'. Are you sure you spelled '{name}' "
            "correctly? If this code used to work and suddenly does not, "
            "this is most probably linked to an update of the tax and "
            "benefit system. Look at its CHANGELOG to learn about renames "
            "and removals and update your code accordingly."
            "Learn more about entities in our documentation:",
            "<https://openfisca.org/doc/coding-the-legislation/50_entities.html>.",
        )
        super().__init__(msg)


__all__ = ["TaxBenefitSystemUnsetError", "VariableNotFoundError"]
