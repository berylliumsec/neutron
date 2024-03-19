import argparse
import os

import requests


def send_request(question: str, server_url: str = "http://localhost:8000"):
    # The default request type is now always 'ask', so we don't need to validate it
    endpoint_url = f"{server_url}/ask"  # The endpoint now directly uses 'ask'

    payload = {"question": question}
    # Retrieve the token from the NEUTRON_TOKEN environment variable
    token = os.environ.get(
        "NEUTRON_TOKEN", "default_token"
    )  # Use a default value if NEUTRON_TOKEN is not set
    headers = {"Authorization": token}  # Use the token from the environment variable
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers)
        if response.status_code == 200:
            # The response from the server is expected to be JSON
            print("Response:", response.json().get("response", "No response received"))
        else:
            # If an error happens, FastAPI will still return JSON formatted error messages
            print(
                "Error:",
                response.status_code,
                response.json().get("detail", "Unknown error"),
            )
    except Exception as e:
        print(f"An error occurred while sending the request: {e}")


def main():
    parser = argparse.ArgumentParser(description="Send a question to the AI server.")
    parser.add_argument("question", type=str, help="The question to ask the AI server.")
    parser.add_argument(
        "--server_url",
        type=str,
        default="http://localhost:8000",
        help="The URL of the AI server, defaults to http://localhost:8000",
    )

    args = parser.parse_args()

    send_request(args.question, args.server_url)


if __name__ == "__main__":
    main()
