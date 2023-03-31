import os
import shutil
import threading
from pathlib import Path
import webbrowser
from git import Repo
from github import Github
from dotenv import load_dotenv
import argparse




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
def create_new_repo(folder_name):
    new_repo = user.create_repo(folder_name)
    return new_repo


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
    new_repo = create_new_repo(folder_name)
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

#Parses command line arguments 
def parse_arguments():
    parser = argparse.ArgumentParser(description="Split a monolithic GitHub repository into separate repositories for each subfolder.")
    parser.add_argument("repo_url", help="URL of the original GitHub repository")
    return parser.parse_args()

def main():
    args = parse_arguments()
    repo_url = args.repo_url

    # Clone the original repository and checkout the destruction branch
    repo = clone_and_checkout(repo_url, CLONE_DIR, DESTRUCTION_BRANCH)

    # Find all subfolders in the cloned repository
    subfolders = find_subfolders()

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

    # Create a README.md file with a table of former contents for the original repository
    create_readme(repo, subfolder_urls)

    # Create a pull request with the changes made in the destruction branch
    pr = create_pull_request(repo)

    # Print the URL of the created pull request
    print(f"Pull request created: {pr.html_url}")

    # Optionally launch an HTML summary of the operation
    launch_summary = input("Would you like to launch an HTML summary? (y/n): ")
    if launch_summary.lower() == "y":
        summary_file = generate_html_summary(subfolder_urls, pr.html_url)
        webbrowser.open(str(summary_file.resolve()))


if __name__ == "__main__":
    main()
