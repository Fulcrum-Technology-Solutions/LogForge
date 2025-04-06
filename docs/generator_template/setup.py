from setuptools import setup, find_packages

setup(
    name="LogForge_example_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "synth_logs",
    ],
    entry_points={
        "synth_logs.generators": [
            "example_generator=example_generator.generator:ExampleGenerator",
        ],
    },
)