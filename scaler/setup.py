from setuptools import setup, find_packages

setup(
    name="scaler",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "paramiko>=3.4.0",
        "pydantic>=2.5.0",
        "rich>=13.7.0",
        "jinja2>=3.1.2",
        "apscheduler>=3.10.4",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "scaler=scaler.cli:main",
            "scaler-wizard=scaler.interactive_scale:main",
        ],
    },
    python_requires=">=3.10",
)







