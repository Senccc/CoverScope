# 🎵 CoverScope - Song Cover Trend Analyzer

CoverScope is a Python Flask web application that analyzes song cover trends on YouTube. Users can search for a song, and the app will fetch cover videos, classify them (vocal, instrumental, etc.), and provide trend analytics, such as an overall trend score and an upload-frequency chart.


## Features

* **YouTube Search:** Fetches up to 50 relevant videos for a song query.

* **Cover Filtering:** Intelligently separates "covers" from "noise" (official videos, lyrics, karaoke).

* **Trend Analytics:** Generates a "Trend Score" based on recency, views, and volume.

* **Data Visualization:** Displays a chart of monthly cover upload frequency.

* **ML Classification:** Uses Scikit-learn (TF-IDF & KMeans) to automatically cluster covers into categories like "Vocal," "Instrumental," "Acoustic," and "Band."

## Tech Stack

* **Backend:** Flask (Python)

* **Frontend:** HTML, CSS, Jinja2

* **API:** YouTube Data API v3

* **Data Science:** Scikit-learn, Numpy

* **Deployment:** Gunicorn (for Render)

## How to Run Locally

1. **Clone the repository:**

```
git clone [your-repo-url] cd song-cover-trends
```

2. **Create and activate a virtual environment:**

```
python -m venv venv source vD/bin/activate # (on Mac/Linux) .\venv\Scripts\activate # (on Windows)
```

3. **Install dependencies:**

```
pip install -r requirements.txt
```

4. **Create your environment file:**

* Create a new file in the root folder named `.env`

* Add your YouTube API key to it:

```
YOUTUBE_API_KEY=YourSecretApiKeyHere
```

5. **Run the app:**

```
flask run
```

The app will be available at `http://127.0.0.1:5000`.