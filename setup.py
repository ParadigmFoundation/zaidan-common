import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='zaidan',
    version='0.0.14',
    author="Henry Harder",
    author_email="henry@paradigm.market",
    description="Common utilities for the Zaidan system.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ParadigmFoundation/zaidan-common",
    packages=setuptools.find_packages(),
    license="MIT",
    install_requires=[
        "json-logging",
        "redis",
        "mysql.connector",
        "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
