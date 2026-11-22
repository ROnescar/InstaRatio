# InstaRatio

A small Flask web app that analyzes your Instagram data export. Upload the ZIP file Instagram gives you, and InstaRatio shows who you follow that doesn't follow you back, and who follows you that you don't follow back.

It never asks for your Instagram password. The ZIP is processed on the machine running the app and the temporary copy is deleted afterward.

## Get your Instagram data

1. In Instagram, go to **Settings → Accounts Center → Your information and permissions → Download your information**.
2. Tap **Download or transfer information** and select your profile.
3. Choose **Some of your information**, then select only **Followers and following**.
4. Set the format to **JSON** and the date range to **All time**, then submit the request.
5. When Instagram emails you, download the ZIP. Do not unzip it.

## Run it locally

Requires Python 3.8+.

```powershell
git clone https://github.com/yourusername/InstaRatio.git
cd InstaRatio
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

On Mac/Linux, activate with `source venv/bin/activate` instead.

Then open http://127.0.0.1:5000 and upload your ZIP. Keep the terminal open while you use the site, and press `Ctrl+C` to stop it.

For development with auto-reload, turn on debug mode first (PowerShell: `$env:FLASK_DEBUG = "1"`). Never enable debug mode on a server that other people can reach.

## Project structure

```
InstaRatio/
├── app.py              # Flask app and ZIP/JSON analysis
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## Security notes

- Uploads are limited to 50 MB, and `.zip` files only.
- JSON files inside the ZIP larger than 100 MB are rejected.
- Files are read from the ZIP in memory by name only, never extracted to disk paths.
- Debug mode is off by default.
- There is no login, so this is meant for personal local use. Add authentication before deploying it publicly.

## Built with

Python, Flask, Jinja2, HTML/CSS.