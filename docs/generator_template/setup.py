from setuptools import setup, find_packages

setup(
    name="LogForge_example_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "logforge",
    ],
    entry_points={
        "logforge.generators": [
            "example_generator=example_generator.generator:ExampleGenerator",
        ],
    },
)