# Github Repo Splitter

This Python script takes a GitHub repository and splits each subfolder into separate repositories while maintaining the commit history. It also updates the original repository with a README.md file containing a "Table of Former Contents" with links to the newly created repositories.

## Prerequisites

- Python 3.7+
- Git installed and configured on your system

## Installation

1. Clone this repository to your local machine.

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root folder of the project and add your GitHub personal access token and the URL of the original repository:

   ```
   GITHUB_ACCESS_TOKEN=your_personal_access_token
   ORIGINAL_REPO_URL=https://github.com/your_username/original_repo.git
   ```

   Replace `your_personal_access_token`, `your_username`, and `original_repo` with your actual information.

## Usage

1. Make sure you are in the root folder of the project and the virtual environment is activated.

2. Run the script:

   ```
   python script.py
   ```

   The script will clone the original repository, create separate repositories for each subfolder, update the original repository's README.md, and create a pull request with the changes.

3. Optionally, the script will prompt you to launch an HTML summary of the operation. If you choose to do so, it will generate an HTML file named `summary.html` and open it in your default web browser. The summary will display links to all the resulting repositories and the created pull request.

## License

This project is licensed under the terms of the MIT license.
