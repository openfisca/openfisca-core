# Extension template

The `policyengine_core.extension_template` module contains a template for an extension. An extension differs from a country model in that it is intended to be used as a plugin to an existing country model, rather than as a standalone model. To create a new extension, simply copy the contents into a new repo, renaming the `extension_template` folder to the name of your extension, then remove the starter code at will. 

Extensions don't have any specific initialisation (unlike a country package, which must define `CountryTaxBenefitSystem`).