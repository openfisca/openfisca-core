## Serve the openfisca Web API.
api:
	$(call print_help,$@:)
	@openfisca serve \
		--country-package openfisca_country_template \
		--extensions openfisca_extension_template
