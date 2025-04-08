from setuptools import setup, find_packages

setup(
    name="logforge",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click>=8.0.0",
        "Jinja2>=3.0.0",
        "PyYAML>=6.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "freezegun>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "logforge=synth_logs.cli:main",
        ],
    },
    python_requires=">=3.8",
)