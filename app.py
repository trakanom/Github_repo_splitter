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

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

app = Flask(__name__)


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


@app.route("/get-username")
def get_username():
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not access_token:
        return jsonify({"username": None})

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    response_json = response.json()
    return jsonify({"username": response_json.get("login")})


@app.route("/clear-token", methods=["POST"])
def clear_token():
    with open(".env", "r") as file:
        lines = file.readlines()

    with open(".env", "w") as file:
        for line in lines:
            if not line.startswith("GITHUB_ACCESS_TOKEN"):
                file.write(line)

    return "", 204


@app.route("/preview", methods=["GET", "POST"])
def preview():
    if request.method == "POST":
        # Process the user's selection and call main() with the selected subfolders
        selected_subfolders = request.form.getlist("subfolder")
        options = {
            "require_preview": False,
            "clear_original_repo": request.form.get("clear_original_repo") == "on",
            "show_summary": request.form.get("show_summary") == "on",
        }
        result = main(request.form["repo_url"], **options)
        return jsonify(result)

    # Render the preview page
    return render_template("preview.html", subfolders=find_subfolders())


if __name__ == "__main__":
    import webbrowser

    webbrowser.open("http://localhost:8000")
    app.run(port=8000)
