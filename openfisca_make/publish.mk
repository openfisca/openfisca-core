## Check for features marked as deprecated.
check-deprecated:
	@$(call help,$@:)
	@python openfisca_core/scripts/find_deprecated.py
