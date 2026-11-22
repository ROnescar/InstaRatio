from flask import Flask, render_template, request
import json
import zipfile
import tempfile
from pathlib import Path

app = Flask(__name__)

def load_json_from_zip(zf, filename):
    """Find a JSON file by its basename, regardless of ZIP folder structure."""
    matches = [name for name in zf.namelist() if Path(name).name.lower() == filename.lower()]
    if not matches:
        return None
    with zf.open(matches[0]) as f:
        return json.load(f)

def extract_usernames(data, mode):
    """Extract usernames from common Instagram export structures."""
    usernames = set()

    if mode == "followers":
        # followers_1.json is normally a list of objects containing string_list_data.
        if isinstance(data, list):
            for person in data:
                try:
                    value = person["string_list_data"][0]["value"]
                    if value:
                        usernames.add(value)
                except (KeyError, IndexError, TypeError):
                    continue

    elif mode == "following":
        # following.json normally contains relationships_following.
        if isinstance(data, dict):
            people = data.get("relationships_following", [])
        else:
            people = data if isinstance(data, list) else []

        for person in people:
            # Your original code uses "title". Keep that as the first option.
            title = person.get("title") if isinstance(person, dict) else None
            if title:
                usernames.add(title)
                continue

            # Some export formats store the username in string_list_data.
            try:
                value = person["string_list_data"][0]["value"]
                if value:
                    usernames.add(value)
            except (KeyError, IndexError, TypeError):
                continue

    return usernames

def analyze_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        followers_data = load_json_from_zip(zf, "followers_1.json")
        following_data = load_json_from_zip(zf, "following.json")

        if followers_data is None:
            raise ValueError("Could not find followers_1.json in the ZIP file.")
        if following_data is None:
            raise ValueError("Could not find following.json in the ZIP file.")

        followers = extract_usernames(followers_data, "followers")
        following = extract_usernames(following_data, "following")

    not_following_back = sorted(following - followers)
    not_following = sorted(followers - following)

    return {
        "followers": len(followers),
        "following": len(following),
        "not_following_back": not_following_back,
        "not_following": not_following,
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        uploaded = request.files.get("instagram_zip")

        if not uploaded or not uploaded.filename:
            error = "Please choose an Instagram ZIP export."
        elif not uploaded.filename.lower().endswith(".zip"):
            error = "Please upload a .zip file."
        else:
            try:
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp:
                    uploaded.save(temp.name)
                    temp_path = Path(temp.name)

                result = analyze_zip(temp_path)
                temp_path.unlink(missing_ok=True)
            except (zipfile.BadZipFile, ValueError, json.JSONDecodeError) as exc:
                error = str(exc)
            except Exception:
                error = "The ZIP could not be processed. Make sure it contains Instagram JSON export files."

    return render_template("index.html", result=result, error=error)

if __name__ == "__main__":
    app.run(debug=True)
