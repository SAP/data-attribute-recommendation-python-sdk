# pylint: disable=missing-module-docstring,missing-function-docstring
from os import path

from setuptools import find_packages, setup


def get_version():
    with open("version.txt") as ver_file:
        version_str = ver_file.readline().rstrip()
    return version_str


def get_long_version():
    # read the contents of your README file
    this_directory = path.abspath(path.dirname(__file__))
    with open(path.join(this_directory, "README.md"), encoding="utf-8") as filehandle:
        long_description = filehandle.read()
    return long_description


setup(
    name="data-attribute-recommendation-sdk",
    version=get_version(),
    description="Data Attribute Recommendation Python SDK",
    long_description=get_long_version(),
    long_description_content_type="text/markdown",
    author="Michael Haas",
    author_email="michael.haas01@sap.com",
    url="https://github.com/sap/data-attribute-recommendation-python-sdk",
    install_requires=[
        "requests~=2.20",
        "typing-extensions~=4.0",
        "cfenv~=0.5",
        "ai-api-client-sdk~=2.4",
        "aenum==3.1.12",
    ],
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    python_requires="~=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
        "License :: OSI Approved :: Apache Software License",
    ],
    project_urls={
        "Documentation": "https://data-attribute-recommendation-python-sdk."
        + "readthedocs.io/en/latest/",
        "Source": "https://github.com/SAP/data-attribute-recommendation-python-sdk",
        "Issue Tracker": "https://github.com/SAP/"
        + "data-attribute-recommendation-python-sdk/issues",
    },
)

# List of classifiers:
# https://pypi.org/classifiers/
# https://www.python.org/dev/peps/pep-0301/#distutils-trove-classification
