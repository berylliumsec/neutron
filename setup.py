from setuptools import find_packages, setup

setup(
    name="neutron-ai",
    version="1.0.0b3",
    description="AI Powered Ethical Hacking Assistant",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="David I",
    author_email="david@berylliumsec.com",
    url="https://github.com/berylliumsec/neutron",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Topic :: Text Processing :: Linguistic",
    ],
    license="BSD",
    keywords="AI, Ethical Hacking",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "neutron": ["images/*"],  # Make sure this reflects the actual structure
    },
    install_requires=[
        "torch>=1.0.1",
        "transformers>=4.34.0",
        "fastapi",
        "uvicorn",
        "pydantic",
        # Add any other dependencies as necessary
    ],
    entry_points={
        "console_scripts": [
            # Allows users to type 'neutron-client' in the command line to interact with the server
            "neutron-client=neutron.client:main",
            # Allows users to start the server by typing 'neutron-server'
            "neutron-server=neutron.server:main",
        ],
    },
    python_requires=">=3.10",
)
