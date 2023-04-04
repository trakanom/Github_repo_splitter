import os
import requests
from dotenv import load_dotenv
import uuid
from flask import (
    Flask,
    request,
    redirect,
    render_template,
    jsonify,
    render_template_string,
    session,
)
from flask_app.main_script import *

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

app = Flask(__name__)
app.secret_key = os.urandom(16)  # Set the secret key for session data

# Import find_subfolders function from main.py
from flask_app.main_script import find_subfolders


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/connect-github")
def connect_github():
    oauth_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=repo"
    return redirect(oauth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}
    response = requests.post(
        "https://github.com/login/oauth/access_token", data=data, headers=headers
    )
    response_json = response.json()

    access_token = response_json.get("access_token")
    if access_token:
        with open(".env", "a") as f:
            f.write(f"\nGITHUB_ACCESS_TOKEN={access_token}")
        return "<script>window.close();</script>"  # Close the new window
    else:
        return redirect("/connect-github")  # Redirect to the landing page


@app.route("/split-repo", methods=["POST"])
def split_repo():
    data = request.get_json()
    preview = data.get("preview", False)
    repo_url = data.get("url")
    if not repo_url:
        return "Error: Missing URL parameter", 400

    try:
        from flask_app.main_script import main

        if not preview:
            # Code to create repositories and push to GitHub
            result = main_script(repo_url)
            return jsonify(
                {
                    "pull_request_url": result["pull_request_url"],
                    "subfolder_urls": result["subfolder_urls"],
                }
            )
        else:
            # Code to only generate a preview of the changes
            preview_data = main_script(repo_url, preview=True)
            session["preview_data"] = preview_data
            return redirect("/preview")
    except Exception as e:
        print(f"Error: {e}")
        return "Error: Failed to split the repository", 500


@app.route("/summary")
def summary():
    subfolder_urls = request.args.getlist("subfolder_urls[]")
    pull_request_url = request.args.get("pull_request_url")

    if not subfolder_urls or not pull_request_url:
        return "Error: Missing URL parameters", 400

    from flask_app.main_script import generate_html_summary

    html_content = generate_html_summary(subfolder_urls, pull_request_url)
    return render_template_string(html_content)


@app.route("/get-username")
def get_username():
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not access_token:
        return jsonify({"username": None})

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    response_json = response.json()

    if response.status_code == 200:
        return jsonify({"username": response_json["login"]})
    else:
        return jsonify({"username": None, "error": response_json.get("message")})


@app.route("/clear-token", methods=["POST"])
def clear_token():
    with open(".env", "r") as file:
        lines = file.readlines()

    with open(".env", "w") as file:
        for line in lines:
            if not line.startswith("GITHUB_ACCESS_TOKEN"):
                file.write(line)

    return "", 204


@app.route("/preview", methods=["POST"])
def preview():
    data = request.get_json()

    if data:
        repo_url = data.get("url")
        selected_subfolders = data.get("subfolder", [])
        options = {
            "require_preview": False,
            "clear_original_repo": data.get("clear_original_repo", False),
            "show_summary": data.get("show_summary", False),
        }
        result = main_script(repo_url, **options)
        return jsonify(result)
    else:
        return "Error: Preview data not available", 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
