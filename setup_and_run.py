import os
import subprocess
import sys
import time
import shutil


def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as error:
        print(f"Error: {error}")
        sys.exit(1)


def setup_and_run():
    npm_executable = shutil.which("npm")
    if not npm_executable:
        print(
            "Error: npm not found. Please make sure Node.js is installed and npm is in your PATH."
        )
        return

    # Install Electron globally
    print("Installing Electron globally...")
    run_command("npm install -g electron")

    # Install project dependencies
    print("Installing project dependencies...")
    run_command("npm install")

    # Installing virtualenv
    print("Installing virtual environment dependencies...")
    run_command("pip install virtualenv")

    # Building virtualenv
    print("Creating virtual environment 'venv'...")
    run_command("virtualenv venv")

    print("Activating venv...")
    run_command(r"venv\Scripts\activate")

    # Install Python requirements
    print("Installing Python requirements...")
    run_command("pip install -r requirements.txt")

    # Run Flask server
    print("Starting Flask server...")
    flask_process = subprocess.Popen(["python", "app.py"], shell=False)

    time.sleep(5)  # Add a delay of 5 seconds to allow the Flask server to start
    # Start the Electron app after starting the Flask server
    print("Starting Electron app...")
    electron_process = subprocess.Popen([npm_executable, "start"], shell=False)
    electron_process.wait()

    # Wait for Electron app to close and terminate Flask server
    try:
        electron_process.wait()
    finally:
        flask_process.terminate()
        print("Electron app closed. Flask server terminated.")


if __name__ == "__main__":
    setup_and_run()
