import os
import requests
from flask import Flask, request, redirect
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

app = Flask(__name__)


@app.route("/")
def home():
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


if __name__ == "__main__":
    app.run(port=8000)
