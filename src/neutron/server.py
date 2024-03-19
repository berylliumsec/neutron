import argparse
import os
from typing import Any, Dict

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
    "--port", type=int, default=8000, help="The port of the webserver. Default is 8000."
)  # FastAPI's default port is 8000
args = parser.parse_args()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

model = InteractiveModel()  # Initializes the model with its default configuration


def check_auth(token: str) -> bool:
    """This function is called to check if a given token is valid."""
    # Retrieve the secret token from the NEUTRON_TOKEN environment variable
    secret_token = os.environ.get(
        "NEUTRON_TOKEN", "default_token"
    )  # Use a default value if NEUTRON_TOKEN is not set
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
        return {"response": response}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={e})
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
