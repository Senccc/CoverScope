from flask import Flask, render_template, request
from utils.youtube_api import search_youtube_covers
from utils.analytics import get_top_covers, calculate_trend_score, generate_trend_summary, get_monthly_upload_data, classify_video_title
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

    # 2. NOW, run analytics ONLY on the clean cover_videos list
    # --- CHANGED: All functions now use cover_videos ---
    top_covers = get_top_covers(cover_videos)
    trend_score = calculate_trend_score(cover_videos)
    trend_summary = generate_trend_summary(trend_score)
    months, upload_counts = get_monthly_upload_data(cover_videos)


    # 3. Run ML on cover videos
    # --- CHANGED: num_clusters is now 4 to match your 4 keyword buckets ---
    labels, cluster_name_map = cluster_cover_videos(cover_videos)

    # Assign cluster labels and names back into each video
    # This part was already 100% correct!
    for video, label in zip(cover_videos, labels):
        video["cluster"] = int(label)
        video["cluster_name"] = cluster_name_map.get(label, "Other")
    
    
    return render_template(
        "results.html",
        videos=videos, # Pass the original full list for the avg view calculation
        song_query=song_query,
        top_covers=top_covers,
        trend_score=trend_score,
        trend_summary=trend_summary,
        months=months,
        upload_counts=upload_counts,
        cover_videos=cover_videos, # This list now contains cluster_name
        noise_videos=noise_videos,
        cover_count=cover_count,
        total_results=total_results
    )


if __name__ == '__main__':
    app.run(debug=True)
