# Introduction

This is the documentation for PolicyEngine Core, the open-source Python package powering PolicyEngine's tax-benefit microsimulation models. It is a fork of [OpenFisca-Core](https://github.com/openfisca/openfisca-core), developed and maintained by [OpenFisca](https://www.openfisca.org/).

PolicyEngine Core does not simulate any specific tax-benefit policy: instead, it is a general framework for building tax-benefit microsimulation models. It is currently used by PolicyEngine UK and PolicyEngine US, which each define the custom logic, parameters and data required to simulate the tax-benefit systems of the UK and the US respectively. 

The country models each provide:

* A set of *entity types* (e.g. `Person`).
* A set of *parameters* (e.g. `Flat tax rate`). Parameters are global data points that have different values for different time periods.
* A set of *variables* (e.g. `Tax liability`). Variables are properties of entities that can be dependent on entities (including other variable values), parameters and the time period.

PolicyEngine Core then enables users to:

* Calculate the value of a variable in a specific time period.
* Trace the computation tree of a calculation.

PolicyEngine Core also includes many helper functions designed to simplify the process of modelling a country's policy.
