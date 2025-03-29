from setuptools import setup, find_packages

setup(
    name="synth_logs",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click>=8.0.0",
        "Jinja2>=3.0.0",
        "PyYAML>=6.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "synth-logs=synth_logs.cli:main",
        ],
        "synth_logs.packages": [
            "windows=packages.windows:register",
            "paloalto=packages.paloalto:register",
            "azure=packages.azure:register",
        ],
    },
    python_requires=">=3.8",
)