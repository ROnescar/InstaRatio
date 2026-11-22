import json
import os
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

# Reject uploads larger than 50 MB before they are read into memory.
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# Refuse any JSON file inside the ZIP that would expand past 100 MB (zip-bomb guard).
MAX_JSON_BYTES = 100 * 1024 * 1024


def load_json_from_zip(zf, filenames):
    """Find the first matching JSON file by basename, regardless of ZIP folder structure."""
    for filename in filenames:
        matches = [
            name for name in zf.namelist()
            if Path(name).name.lower() == filename.lower()
        ]
        if not matches:
            continue

        info = zf.getinfo(matches[0])
        if info.file_size > MAX_JSON_BYTES:
            raise ValueError(f"{filename} is too large to process.")

        with zf.open(info) as f:
            return json.load(f)

    return None


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
            # The username is usually stored in "title".
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
        followers_data = load_json_from_zip(zf, ["followers_1.json", "followers.json"])
        following_data = load_json_from_zip(zf, ["following.json", "following_1.json"])

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


@app.errorhandler(413)
def file_too_large(_error):
    return render_template(
        "index.html",
        result=None,
        error="That file is too large. The upload limit is 50 MB.",
    ), 413


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
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp:
                    uploaded.save(temp)
                    temp_path = Path(temp.name)

                result = analyze_zip(temp_path)
            except (zipfile.BadZipFile, ValueError, json.JSONDecodeError) as exc:
                error = str(exc)
            except Exception:
                error = "The ZIP could not be processed. Make sure it contains Instagram JSON export files."
            finally:
                # Always delete the temp file, even if processing failed.
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    # Debug mode is OFF unless you explicitly turn it on for local development:
    #   PowerShell:  $env:FLASK_DEBUG = "1"
    #   Mac/Linux:   export FLASK_DEBUG=1
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")