## Install openfisca-core for deployment and publishing.
build: setup.py
	@## This allows us to be sure tests are run against the packaged version
	@## of openfisca-core, the same we put in the hands of users and reusers.
	@$(call help,$@:)
	@python $? bdist_wheel
	@find dist -name "*.whl" -exec pip install --force-reinstall {}[dev] \;
