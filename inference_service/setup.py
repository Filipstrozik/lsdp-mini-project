from setuptools import setup, find_packages

setup(
    name="inference_service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "grpcio",
        "grpcio-tools",
        "torch",
        "transformers",
        "pyspark",
        "protobuf",
        "numpy",
    ],
    python_requires=">=3.12",
)
