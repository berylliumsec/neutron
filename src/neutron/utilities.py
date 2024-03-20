import json
import logging
import os
import shutil
import socket
import subprocess
import sys
from importlib.metadata import version
from zipfile import ZipFile

import requests
import transformers
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

transformers.logging.set_verbosity_error()
model_s3_url = "https://nebula-pro-beta.s3.amazonaws.com/neutron_model.zip"  # Update this with your actual S3 URL
chroma_s3_url = "https://nebula-pro-beta.s3.amazonaws.com/neutron_chroma.db.zip"
# Configure basic logging
# This will set the log level to ERROR, meaning only error and critical messages will be logged
# You can specify a filename to write the logs to a file; otherwise, it will log to stderr
log_file_path = os.path.join(os.path.expanduser("~"), "neutron.log")
# Configure basic logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure basic logging
# Get the user's home directory from the HOME environment variable
home_directory = os.getenv("HOME")  # This returns None if 'HOME' is not set

if home_directory:
    log_file_path = os.path.join(home_directory, "neutron.log")
else:
    # Fallback mechanism or throw an error
    log_file_path = (
        "neutron.log"  # Default to current directory, or handle error as needed
    )


def get_input_with_default(message, default_text=None):
    style = Style.from_dict({"prompt": "cyan", "info": "cyan"})
    history = InMemoryHistory()
    if default_text:
        user_input = prompt(message, default=default_text, history=history, style=style)
    else:
        user_input = prompt(message, history=history, style=style)
    return user_input


def ensure_model_folder_exists(model_directory, auto_update=True):
    if model_directory == "neutron_model":
        s3_url = model_s3_url
    else:
        s3_url = chroma_s3_url
    try:
        metadata_file = os.path.join(model_directory, "metadata.json")

        try:
            local_etag = get_local_metadata(metadata_file)
        except Exception as e:
            logging.error(f"Error getting local metadata: {e}")

        try:
            s3_etag = get_s3_file_etag(s3_url)
        except Exception as e:
            logging.error(f"Error getting S3 file etag: {e}")

        if s3_etag is None:
            logging.warning(
                "No S3 etag found. Possibly no internet connection or issue with S3."
            )

        # Check if the model directory exists and has the same etag (metadata)
        if folder_exists_and_not_empty(model_directory) and local_etag == s3_etag:
            logging.info(f"Model directory {model_directory} is up-to-date.")
            return  # No need to update anything as local version matches S3 version

        if not auto_update:
            # If folder doesn't exist, is empty, or etag doesn't match, prompt for download.
            try:
                user_input = get_input_with_default(
                    "New versions of the models are available, would you like to download them? (y/n) ",
                    default_text="y",  # Automatically opt for download if not specified otherwise
                )
            except Exception as e:
                logging.error(f"Error getting user input: {e}")
                return

            if user_input.lower() != "y":
                logging.info("User chose not to update the model directory.")
                return  # Exit if user chooses not to update
        else:
            logging.info(
                "Auto-update is enabled. Downloading new version if necessary..."
            )

        # Proceed with the removal of the existing model directory and the download of the new version
        if os.path.exists(model_directory):
            logging.info("Removing existing model folder...")
            try:
                shutil.rmtree(model_directory)
            except Exception as e:
                logging.error(f"Error removing existing model directory: {e}")
                return

        logging.info(
            f"{model_directory} not found or is outdated. Downloading and unzipping..."
        )
        try:
            download_and_unzip(s3_url, f"{model_directory}.zip")
            # Save new metadata
            save_local_metadata(metadata_file, s3_etag)
        except Exception as e:
            logging.error(f"Error updating model directory: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def is_run_as_package():
    if os.environ.get("IN_DOCKER"):
        return False
    return "site-packages" in os.path.abspath(__file__)


def folder_exists_and_not_empty(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return False
    # Check if the folder is empty
    if not os.listdir(folder_path):
        return False
    return True


def download_and_unzip(url, output_name):
    try:
        # Download the file from the S3 bucket using wget with progress bar
        logging.info("Downloading...")
        subprocess.run(
            ["wget", "--progress=bar:force:noscroll", url, "-O", output_name],
            check=True,
        )

        # Define the target directory based on the intended structure
        target_dir = os.path.splitext(output_name)[0]  # Removes '.zip' from output_name

        # Extract the ZIP file
        logging.info("\nUnzipping...")
        with ZipFile(output_name, "r") as zip_ref:
            # Here we will extract in a temp directory to inspect the structure
            temp_dir = "temp_extract_dir"
            zip_ref.extractall(temp_dir)

            # Check if there is an unwanted nested structure
            extracted_dirs = os.listdir(temp_dir)
            if len(extracted_dirs) == 1 and os.path.isdir(
                os.path.join(temp_dir, extracted_dirs[0])
            ):
                nested_dir = os.path.join(temp_dir, extracted_dirs[0])
                # Move content up if there is exactly one directory inside
                if os.path.basename(nested_dir) == output_name:
                    shutil.move(nested_dir, target_dir)
                else:
                    shutil.move(nested_dir, os.path.join(target_dir, output_name))
            else:
                # No nested structure, so just move all to the target directory
                os.makedirs(target_dir, exist_ok=True)
                for item in extracted_dirs:
                    shutil.move(
                        os.path.join(temp_dir, item), os.path.join(target_dir, item)
                    )

            # Cleanup temp directory
            shutil.rmtree(temp_dir)

        # Remove the ZIP file to clean up
        os.remove(output_name)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred during download: {e}")
        logging.error(f"Error occurred during download: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        logging.error(f"Unexpected error: {e}")


def save_local_metadata(file_name, etag):
    with open(file_name, "w") as f:
        json.dump({"etag": etag}, f)


def return_path(path):
    if is_run_as_package():
        return path
    else:
        return resource_path(path)


def is_internet_available(host="8.8.8.8", port=53, timeout=3):
    """Check if there is an internet connection."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def get_s3_file_etag(s3_url):
    if not is_internet_available():
        logging.error("No internet connection available. Skipping version check.")
        return None
    response = requests.head(s3_url)
    return response.headers.get("ETag")


def get_local_metadata(file_name):
    try:
        with open(file_name, "r") as f:
            data = json.load(f)
            return data.get("etag")
    except FileNotFoundError:
        return None


def get_latest_pypi_version(package_name):
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        if response.status_code == 200:
            return response.json()["info"]["version"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get latest version information: {e}")
    return None


def check_new_pypi_version(package_name="neutron-ai"):
    """Check if a newer version of the package is available on PyPI."""
    if not is_internet_available():
        logging.error("No internet connection available. Skipping version check.")
        return

    try:
        installed_version = version(package_name)
    except Exception as e:
        logging.error(f"Error retrieving installed version of {package_name}: {e}")
        return

    print(f"Installed version: {installed_version}")

    try:
        latest_version = get_latest_pypi_version(package_name)
        if latest_version is None:
            logging.error(
                f"Error retrieving latest version of {package_name} from PyPI."
            )
            return

        if latest_version > installed_version:
            print(
                f"A newer version ({latest_version}) of {package_name} is available on PyPI. Please consider updating to access the latest features!"
            )
    except Exception as e:
        logging.error(f"An error occurred while checking for the latest version: {e}")
