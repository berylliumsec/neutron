import argparse
import os
from typing import Any, Dict

import psutil
import torch
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from neutron.interactive_model import InteractiveModel

# Set up argument parsing
parser = argparse.ArgumentParser(description="Run the FastAPI server.")
parser.add_argument(
    "--host",
    type=str,
    default="0.0.0.0",
    help="The hostname to listen on. Default is 0.0.0.0.",
)
parser.add_argument(
    "--port",
    type=int,
    default=8000,
    help="The port of the webserver. Default is 8000."
)
parser.add_argument(
    "--model_name",
    type=str,
    default="deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    help="The name of the model to load. Default is DeepSeek-R1-Distill-Llama-8B.",
)
parser.add_argument(
    "--cache_dir",
    type=str,
    default="/media/agent/dige-backup/cache",
    help="Where to store the downloaded model",
)
parser.add_argument(
    "--disable_search",
    action="store_true",
    help="Disable DuckDuckGo search functionality.",
)
args = parser.parse_args()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

if not torch.cuda.is_available():
    print("At least 8GB of GPU is required for Neutron to run")
    exit(0)

# Initialize the InteractiveModel with the selected model name and search setting.
model = InteractiveModel(
    model_name=args.model_name,
    use_search=not args.disable_search,
    cache_dir = args.cache_dir
)

# Get current process ID and memory info
pid = os.getpid()
process = psutil.Process(pid)
memory_use = process.memory_info().rss
memory_use_gb = memory_use / 1024 / 1024 / 1024
print(f"Memory used by Neutron: {memory_use_gb:.2f} GB")
print(
    "Neutron is now part of Nebula Pro's Free Tier.\n"
    "Embrace the future of AI Powered Ethical Hacking with Nebula Pro ->> "
    "https://www.berylliumsec.com/nebula-pro-waitlist "
)


def check_auth(token: str) -> bool:
    """Check if a given token is valid."""
    # Retrieve the secret token from the NEUTRON_TOKEN environment variable
    secret_token = os.environ.get("NEUTRON_TOKEN", "default_token")
    return token == secret_token


class Query(BaseModel):
    question: str


@app.post("/ask")
def ask(request: Request, query: Query) -> Dict[str, Any]:
    # Check for auth token
    auth_token = request.headers.get("Authorization")
    if not auth_token or not check_auth(auth_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    try:
        response = model.invoke(query.question)
        memory_use = process.memory_info().rss
        memory_use_gb = memory_use / 1024 / 1024 / 1024
        print(f"Memory used by Neutron: {memory_use_gb:.2f} GB")
        return {"response": response}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


def main():
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
