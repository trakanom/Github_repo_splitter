import os
import shutil
import threading
from pathlib import Path
import webbrowser
from git import Repo
from github import Github
from dotenv import load_dotenv
import argparse
import shutil
from flask import session

load_dotenv()

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
CLONE_DIR = "clone_temp"
DESTRUCTION_BRANCH = "destruction"

github_instance = Github(GITHUB_ACCESS_TOKEN)
user = github_instance.get_user()

# Clone the specified repository and checkout a new branch
def clone_and_checkout(repo_url, clone_dir, branch):
    repo = Repo.clone_from(repo_url, clone_dir)
    repo.git.checkout("-b", branch)
    return repo


# Create a new GitHub repository with the specified folder name
def create_repo(token, repo_name):
    g = Github(token)
    user = g.get_user()

    try:
        user.create_repo(repo_name)
        print(f'Repository "{repo_name}" created successfully.')
    except Exception as e:
        if "name already exists on this account" in str(e):
            print(f'Repository "{repo_name}" already exists.')
        else:
            print("An unexpected error occurred:", e)


def delete_repo(token, repo_name):
    g = Github(token)
    user = g.get_user()

    try:
        repo = user.get_repo(repo_name)
        repo.delete()
        print(f'Repository "{repo_name}" deleted successfully.')
    except Exception as e:
        if "Not Found" in str(e):
            print(f'Repository "{repo_name}" not found.')
        else:
            print("An unexpected error occurred:", e)


# Extract and push the specified subfolder to the new repository
def extract_and_push_subfolder(repo, folder_name, new_repo):
    repo.git.filter_repo("--subdirectory-filter", folder_name, "--force")
    repo.git.push(new_repo.clone_url, f"HEAD:main", force=True)


# Verify if the subfolder has been pushed to the new repository
def verify_push(new_repo, folder_name):
    contents = new_repo.get_contents("")
    for file in contents:
        if file.name == folder_name:
            return True
    return False


# Remove the specified subfolder from the original repository and push the changes
def remove_subfolder_and_push(repo, folder_name):
    shutil.rmtree(folder_name)
    repo.git.add(update=True)
    repo.git.commit("-m", f"Remove {folder_name}")
    repo.git.push()


# Handle the specified subfolder by creating a new repository, pushing the subfolder to it,
# and removing the subfolder from the original repository
def handle_subfolder(repo, folder_name):
    new_repo = create_repo(folder_name)
    extract_and_push_subfolder(repo, folder_name, new_repo)
    if verify_push(new_repo, folder_name):
        remove_subfolder_and_push(repo, folder_name)
    return new_repo.html_url


# Process all the subfolders in the original repository
def process_subfolders(repo, subfolders):
    urls = []
    for folder in subfolders:
        url = handle_subfolder(repo, folder)
        urls.append(url)
    return urls


# Find all the subfolders in the cloned repository
def find_subfolders():
    subfolders = [
        f.name
        for f in os.scandir(CLONE_DIR)
        if f.is_dir() and not f.name.startswith(".")
    ]
    return subfolders


# Create a README.md file in the original repository with a table of former contents
def create_readme(repo, subfolder_urls):
    readme_content = "# Table of Former Contents\n\n"
    for url in subfolder_urls:
        readme_content += f"- [{url.split('/')[-1]}]({url})\n"
    with open("README.md", "w") as readme_file:
        readme_file.write(readme_content)
    repo.git.add("README.md")
    repo.git.commit("-m", "Create README.md with Table of Former Contents")
    repo.git.push()


# Create a pull request with the changes made in the destruction branch
def create_pull_request(repo):
    base = repo.default_branch
    head = DESTRUCTION_BRANCH
    pr = repo.create_pull(
        title="Destruction Branch",
        body="This branch contains the destructive changes.",
        base=base,
        head=head,
    )
    return pr


# Generate an HTML summary of the split repositories and the pull request
def generate_html_summary(subfolder_urls, pr_url):
    html_content = f"""
    <html>
        <head>
            <title>Repo Split Summary</title>
        </head>
        <body>
            <h1>Newly Created Repositories</h1>
            <ul>
                {''.join([f'<li><a href="{url}">{url.split("/")[-1]}</a></li>' for url in subfolder_urls])}
            </ul>
            <h1>Pull Request</h1>
            <a href="{pr_url}">{pr_url}</a>
        </body>
    </html>
    """
    summary_file = Path("summary.html")
    summary_file.write_text(html_content)
    return summary_file


# Parses command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Split a monolithic GitHub repository into separate repositories for each subfolder."
    )
    parser.add_argument("repo_url", help="URL of the original GitHub repository")
    return parser.parse_args()


def is_github_authorized():
    return "GITHUB_ACCESS_TOKEN" in os.environ


import shutil


def main_script(
    repo_url,
    subfolders=None,
    preview=False,
    require_preview=False,
    clear_original_repo=False,
    show_summary=False,
):

    if not is_github_authorized():
        raise Exception("GitHub authorization is required")

    if not is_github_authorized():
        print(
            "Please visit http://localhost:8000/frontend to authorize this application on GitHub."
        )
        return

    repo_url = repo_url

    # Remove the clone_temp directory if it exists
    if os.path.exists(CLONE_DIR) and os.path.isdir(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)

    # Clone the original repository and checkout the destruction branch
    repo = clone_and_checkout(repo_url, CLONE_DIR, DESTRUCTION_BRANCH)

    # Find all subfolders in the cloned repository
    if subfolders is None:
        subfolders = find_subfolders()

    if preview or require_preview:
        # Store the subfolders in the session and retrieve them later in the splitting process
        session["subfolders"] = subfolders
        return

    # Retrieve the subfolders from the session if they were set in the preview step
    subfolders = session.get("subfolders", subfolders)

    # Create a separate thread for each subfolder to handle the splitting process
    threads = []
    for folder in subfolders:
        thread = threading.Thread(target=handle_subfolder, args=(repo, folder))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete execution
    for thread in threads:
        thread.join()

    # Process the subfolders and obtain the URLs of the new repositories
    subfolder_urls = process_subfolders(repo, subfolders)

    if clear_original_repo:
        # Create a README.md file with a table of former contents for the original repository
        create_readme(repo, subfolder_urls)

        # Create a pull request with the changes made in the destruction branch
        pr = create_pull_request(repo)
        pull_request_url = pr.html_url
    else:
        pull_request_url = None

    if show_summary:
        # Generate an HTML summary of the split repositories and the pull request
        summary_file = generate_html_summary(subfolder_urls, pull_request_url)
        # You can open the summary_file in a browser or return its content

    return {"subfolder_urls": subfolder_urls, "pull_request_url": pull_request_url}


# Update the __main__ block
# if __name__ == "__main__":
# import argparse

# parser = argparse.ArgumentParser(
#     description="Split a monolithic GitHub repository into separate repositories for each subfolder."
# )
# parser.add_argument("repo_url", help="URL of the original GitHub repository")
# args = parser.parse_args()

# result = main_script(args.repo_url)
# print(f"Pull request created: {result['pull_request_url']}")