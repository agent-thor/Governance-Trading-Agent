from setuptools import setup, find_packages

setup(
    name="proposal_revamp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "python-dotenv",
        "firebase-admin",
        "python-binance",
        "torch",
        "transformers",
        "beautifulsoup4",
        "flask",
        "boto3",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "governance-bot=proposal_revamp.main:main",
        ],
    },
    author="Krishna Yadav",
    author_email="krishna@example.com",
    description="Governance Trading Bot for cryptocurrency trading based on governance proposals",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 