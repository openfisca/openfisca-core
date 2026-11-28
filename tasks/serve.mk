## Serve the openfisca Web API.
api:
	@$(call print_help,$@:)
	@openfisca serve \
		--extensions openfisca_extension_template
