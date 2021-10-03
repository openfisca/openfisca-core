## Install openfisca-core for deployment and publishing.
build:
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call print_help,$@:)
	@python setup.py bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall {}[dev] \;

## Check for features marked as deprecated.
check-deprecated:
	@$(call print_help,$@:)
	@python -m openfisca_tasks CheckDeprecated
	@$(call print_pass,$@:)

## Check if the current version is acceptable.
check-version:
	@$(call help,$@:)
	@python -m openfisca_tasks CheckVersion
	@$(call print_pass,$@:)
