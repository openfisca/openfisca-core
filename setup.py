from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of our README file for PyPi
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Please make sure to cap all dependency versions, in order to avoid unwanted
# functional and integration breaks caused by external code updates.

general_requirements = [
    "pytest>=4,<6",
    "numpy>=1.11,<1.21",
    "black",
    "linecheck",
    "yaml-changelog",
    "coverage",
    "sortedcontainers",
    "numexpr",
    "dpath",
    "nptyping<2",
    "psutil",
    "wheel",
]

dev_requirements = [
    "jupyter-book",
    "furo",
    "markupsafe==2.0.1",
]

setup(
    name="policyengine-core",
    version="1.0.4",
    author="PolicyEngine",
    author_email="hello@policyengine.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="A versatile microsimulation free software",
    keywords="benefit microsimulation social tax",
    license="https://www.fsf.org/licensing/licenses/agpl-3.0.html",
    license_files=("LICENSE",),
    url="https://github.com/openfisca/openfisca-core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    data_files=[
        (
            "share/openfisca/openfisca-core",
            ["README.md"],
        ),
    ],
    entry_points={
        "console_scripts": [
            "policyengine-core=policyengine_core.scripts.policyengine_command:main",
        ],
    },
    extras_require={
        "dev": dev_requirements,
    },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=general_requirements,
    packages=find_packages(exclude=["tests*"]),
)
