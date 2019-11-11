import setuptools
import unittest


def get_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('test', pattern='*_test.py')
    return test_suite


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='zaidan',
    version='0.0.22',
    author="Henry Harder",
    author_email="henry@paradigm.market",
    description="Common utilities for the Zaidan system.",
    long_description=long_description,
    test_suite="setup.get_test_suite",
    long_description_content_type="text/markdown",
    url="https://github.com/ParadigmFoundation/zaidan-common",
    packages=setuptools.find_packages(),
    license="MIT",
    install_requires=[
        "json-logging",
        "redis",
        "mysql-connector",
        "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
