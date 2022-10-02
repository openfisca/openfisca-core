"""
This module directs PyTest to include certain global fixtures when running tests. 
"""

pytest_plugins = [
    "tests.fixtures.entities",
    "tests.fixtures.simulations",
    "tests.fixtures.taxbenefitsystems",
]
