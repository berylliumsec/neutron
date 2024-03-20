# Neutron

Welcome to Neutron.

![Neutron](/images/neutron.png)

## Galaxy

- [Neutron](#Neutron)
  - [Galaxy](#galaxy)
  - [Acknowledgement](#acknowledgement)
  - [Why Neutron?](#why-Neutron)
  - [Compatibility](#compatibility)
  - [System dependencies and installation](#system-dependencies)
  - [Upgrading](#upgrading)
  - [Usage.](#usage)



## Acknowledgement

**First i would like to thank the All-Mighty God who is the source of all knowledge, without Him, this would not be possible.**

## **Disclaimer: AI can make mistakes, consider cross-checking suggestions.**

## 🌐 Introducing Nebula Pro: A New Era in Ethical Hacking 🌐

🚀 We're thrilled to unveil a sneak peek of Nebula Pro, our latest innovation designed to empower ethical hackers with advanced, AI-driven capabilities. After months of dedicated development, we have launched the preview version. Some of the exciting features are:

- AI Powered Autonomous Mode
- AI Powered Suggestions
- AI Powered Note Taking

**Neutron will become a part of Nebula Pro's free tier**
# 📺 [Click Here to Get Access To Nebula Pro Now](https://www.berylliumsec.com/nebula-pro-waitlist) 🚀



## Why Neutron?

The purpose of Neutron is straightforward: to provide security professionals  with access to a free AI assistant that can be invoked directly from their command line interface. It was built as part of the free tier of [Nebula Pro](https://www.berylliumsec.com/nebula-pro-waitlist).

## [Click Here to Watch Neutron in Action](https://youtu.be/v5X8TNPsMbM)


## Compatibility

Neutron has been extensively tested and optimized for Linux platforms. As of now, its functionality on Windows or macOS is not guaranteed, and it may not operate as expected.

## System dependencies

- Storage: A minimum of 50GB is recommended.

- RAM: A minimum of 16GB RAM memory is recommended.

- Graphics Processing Unit (GPU) (NOT MANDATORY, Neutron can run on CPU): While not mandatory, having at least 24GB of GPU memory is recommended for optimal performance.


**PYPI based distribution requirement(s)**

- Python3: Version 3.10 or later is required for compatibility with all used libraries.
- PyTorch: A machine learning library for Python, used for computations and serving as a foundation for the Transformers library.
- Transformers library by Hugging Face: Provides state-of-the-art machine learning techniques for natural language processing tasks.      Required for models and tilities used in NLP operations.
- FastAPI: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
- Uvicorn: An ASGI server for Python, needed to run FastAPI applications.
- Pydantic: Data validation and settings management using Python type annotations, utilized within FastAPI applications.
- Langchain Community and Core libraries : Utilized for specific functionalities related to embeddings, vector stores, and more in the context of language processing.
- Regular Expressions (re module in Python Standard Library): Utilized for string operations
- Requests library

To install the above dependencies:

```bash
pip install fastapi uvicorn pydantic torch transformers regex argparse typing-extensions langchain_community langchain_core

```

**PIP**:

```
pip install neutron-ai
```

## Upgrading

For optimal performance and to ensure access to the most recent advancements, we consistently release updates and refinements to our models. Neutron will proactively inform you of any available updates to the package or the models upon each execution.

PIP:

```bash
pip install neutron-ai --upgrade
```

## Usage.

### Server

``` bash
usage: server.py [-h] [--host HOST] [--port PORT]

Run the FastAPI server.

options:
  -h, --help   show this help message and exit
  --host HOST  The hostname to listen on. Default is 0.0.0.0.
  --port PORT  The port of the webserver. Default is 8000.
```

The server can be invoked using the following command after installation using pip:

```
neutron-server 0.0.0.0 8000
```

### Client

```bash
usage: client.py [-h] [--server_url SERVER_URL] question

Send a question to the AI server.

positional arguments:
  question              The question to ask the AI server.

options:
  -h, --help            show this help message and exit
  --server_url SERVER_URL
                        The URL of the AI server, defaults to http://localhost:8000
```

The client can be invoked using the following command after installation using pip:

```bash
neutron-client "your question"
```


To use Neutron AI directly from the command line using a shorter alias for example AN, add the following function to your .bashrc or .zshrc:

```bash
function AN() {
    local query=\"$*\"
    neutron-client \"\$query\"
}
```
After adding, restart your terminal or run 'source ~/.bashrc' (or 'source ~/.zshrc') to apply the changes.

Then after starting the server, you can ask your questions like so:

```bash
AN your question
```

### Authentication

To use a password for the server and client simply add it to your ENVs before you run the server and the client like so:

```bash
export NEUTRON_TOKEN="YOUR_SECRET"
```