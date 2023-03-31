import os
import requests
from flask import (
    Flask,
    request,
    redirect,
    render_template,
    jsonify,
    render_template_string,
)
from dotenv import load_dotenv

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

app = Flask(__name__)
load_dotenv()


@app.route("/frontend")
def frontend():
    return render_template("index.html")


@app.route("/")
def home():
    return render_template("landing.html")


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
        return "Authorization successful. You can now run the main.py script."
    else:
        return "Authorization failed."


@app.route("/split-repo", methods=["POST"])
def split_repo():
    repo_url = request.args.get("url")
    if not repo_url:
        return "Error: Missing URL parameter", 400

    try:
        from main import main

        result = main(repo_url)
        return jsonify(
            {
                "pull_request_url": result["pull_request_url"],
                "subfolder_urls": result["subfolder_urls"],
            }
        )
    except Exception as e:
        print(f"Error: {e}")
        return "Error: Failed to split the repository", 500


@app.route("/summary")
def summary():
    subfolder_urls = request.args.getlist("subfolder_urls[]")
    pull_request_url = request.args.get("pull_request_url")

    if not subfolder_urls or not pull_request_url:
        return "Error: Missing URL parameters", 400

    from main import generate_html_summary

    html_content = generate_html_summary(subfolder_urls, pull_request_url)
    return render_template_string(html_content)


if __name__ == "__main__":
    import webbrowser

    webbrowser.open("http://localhost:8000")
    app.run(port=8000)
