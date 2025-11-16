from flask import Flask, render_template, request
from utils.youtube_api import search_youtube_covers
from utils.analytics import (
    get_top_covers, calculate_trend_score, generate_trend_summary, 
    get_monthly_upload_data, classify_video_title, classify_cover_type
)
from utils.ml_classifier import cluster_cover_videos

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/results", methods=["GET", "POST"])
def results():
    if request.method == "POST":
        song_query = request.form.get("song")
    else:
        song_query = request.args.get("song")

    if not song_query:
        return render_template("results.html", videos=[], song_query="")

    videos = search_youtube_covers(song_query)
    total_results = len(videos)

    # 1. Classify videos first
    cover_videos = []
    noise_videos = []
    for video in videos:
        classification = classify_video_title(video['title'])
        if classification == 'cover':
            cover_videos.append(video)
        else:
            noise_videos.append(video)
    
    cover_count = len(cover_videos)

    # 2. Run analytics ONLY on the clean cover_videos list
    top_covers = get_top_covers(cover_videos)
    trend_score = calculate_trend_score(cover_videos)
    trend_summary = generate_trend_summary(trend_score)
    months, upload_counts = get_monthly_upload_data(cover_videos)


    # 3. Run ML on cover videos
    cluster_results = cluster_cover_videos(cover_videos, song_query=song_query)
    labels = cluster_results["labels"]
    cluster_name_map = cluster_results["cluster_name_map"]
    plot_data = cluster_results["plot_data"]
    top_keywords = cluster_results["top_keywords"]

    # Assign cluster labels and names back into each video
    for i, video in enumerate(cover_videos):
        # Add Stable, Rule-Based data
        rule_classification = classify_cover_type(video)
        video["rule_name"] = rule_classification["name"]
        video["rule_icon"] = rule_classification["icon"]
        
        # Add Volatile, ML-Based data
        ml_label = labels[i]
        video["ml_name"] = cluster_name_map.get(ml_label, "Other")
    
    
    return render_template(
        "results.html",
        videos=videos, 
        song_query=song_query,
        top_covers=top_covers,
        trend_score=trend_score,
        trend_summary=trend_summary,
        months=months,
        upload_counts=upload_counts,
        cover_videos=cover_videos,
        noise_videos=noise_videos,
        cover_count=cover_count,
        total_results=total_results,
        plot_data=plot_data,
        top_keywords=top_keywords
    )


if __name__ == '__main__':
    app.run(debug=True)
