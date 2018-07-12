import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="SQUANCH",
    version="1.0.0",
    author="Ben Bartlett",
    author_email="benbartlett@stanford.edu",
    description="Simulator for Quantum Networks and Channels",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/att-innovate/squanch",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "numpy",
        "tqdm"
    ],
)