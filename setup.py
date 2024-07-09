from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="papys",
    version="0.5.0",
    author="Ronny Fuchs",
    author_email="info@asderix.com",
    description="Python Rest-API as a DAG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://papys.asderix.com/",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    license="Apache 2.0",
)
