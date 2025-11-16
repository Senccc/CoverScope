# utils/ml_classifier.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE  
import numpy as np
import re

# Keyword buckets (English + Japanese)
VOCAL_KEYWORDS = [
    "vocal", "vocals", "a cappella", "a-capella", "vocal cover", "sing",
    "歌ってみた", "ボーカル", "ボーカルカバー", "アカペラ"
]

INSTRUMENTAL_KEYWORDS = [
    "instrumental", "inst", "instrumental cover", "piano", "guitar", 
    "drum", "bass", "solo", "弾いてみた", "インスト", "ピアノ", "ギター"
]

ACOUSTIC_KEYWORDS = [
    "acoustic", "acoustic version", "unplugged", "アコースティック", "アコギ"
]

BAND_KEYWORDS = [
    "band", "full band", "arrangement", "バンドカバー", "編成", "full arrangement"
]

FALLBACK_NAME = "Other / Remix"

def _text_for_video(v):
    # Combine title + description (lowercase); keep original for Japanese matching too
    title = v.get("title", "")
    desc = v.get("description", "") or ""
    return (title + " " + desc).strip()

def _count_matches(text_lower, keywords):
    # simple substring match (case-insensitive)
    count = 0
    for kw in keywords:
        if kw in text_lower:
            count += 1
    return count

def map_clusters_to_names(videos, labels):
    """
    Given videos (list of dicts) and labels (list/array),
    return a dict: cluster_index -> human-readable name
    """
    cluster_texts = {}
    for v, lab in zip(videos, labels):
        cluster_texts.setdefault(lab, []).append(_text_for_video(v).lower())

    mapping = {}
    for lab, texts in cluster_texts.items():
        # aggregate counts per keyword group
        vocal_count = sum(_count_matches(t, VOCAL_KEYWORDS) for t in texts)
        inst_count  = sum(_count_matches(t, INSTRUMENTAL_KEYWORDS) for t in texts)
        acou_count  = sum(_count_matches(t, ACOUSTIC_KEYWORDS) for t in texts)
        band_count  = sum(_count_matches(t, BAND_KEYWORDS) for t in texts)

        # choose the highest hit group
        counts = {
            "Vocal cover": vocal_count,
            "Instrumental": inst_count,
            "Acoustic / Soft": acou_count,
            "Band / Full Arrangement": band_count
        }

        # pick max; if all zero, fallback
        best_name, best_val = max(counts.items(), key=lambda kv: kv[1])
        if best_val == 0:
            mapping[lab] = FALLBACK_NAME
        else:
            mapping[lab] = best_name

    return mapping

def get_top_keywords_per_cluster(kmeans, vectorizer, cluster_name_map, n_keywords=5):
    """
    Finds the top N keywords (TF-IDF features) for each named cluster.
    """
    try:
        keywords = {}
        # Get the words for each feature index
        terms = vectorizer.get_feature_names_out()
        # Get the "center" of each cluster
        cluster_centers = kmeans.cluster_centers_
        
        # Get the original cluster index (0, 1, 2, 3) for each cluster name
        name_to_index = {}
        for idx, name in cluster_name_map.items():
            # Handle potential duplicate names (e.g., two clusters map to "Other")
            if name not in name_to_index:
                name_to_index[name] = idx
            
        for name, idx in name_to_index.items():
            # Get the scores for this cluster's center
            center = cluster_centers[idx]
            # Find the indices of the top N keywords
            top_indices = np.argsort(center)[::-1][:n_keywords]
            # Map indices to words
            top_terms = [terms[i] for i in top_indices]
            keywords[name] = top_terms
            
        return keywords
    except Exception as e:
        print(f"Error getting top keywords: {e}")
        return {} # Return empty on error

def cluster_cover_videos(videos, max_features=800):
    """
    videos: list of dicts (each must have title and description)
    returns: (labels_list, cluster_index_to_name_dict)
    """
    num_clusters = 4
    
    # If we have fewer videos than clusters (e.g., 2 videos, 4 clusters),
    # or no videos at all, clustering is impossible.
    # So, we'll just assign them all to the fallback group (cluster 0).
    if len(videos) < num_clusters:
        labels_list = [0] * len(videos) # e.g., [0, 0] if len(videos) == 2
        cluster_name_map = { 0: FALLBACK_NAME }
        return labels_list, cluster_name_map

    corpus = [_text_for_video(v) for v in videos]

    # TF-IDF - note: 'english' stop words is fine; Japanese tokens will still pass through
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        ngram_range=(1, 2)
    )
    X = vectorizer.fit_transform(corpus)

    # KMeans
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    # Map each cluster to a human name via keyword counting
    cluster_name_map = map_clusters_to_names(videos, labels)

    # Get top keywords for each cluster
    top_keywords = get_top_keywords_per_cluster(kmeans, vectorizer, cluster_name_map)
    
    # Run t-SNE for 2D plot data
    # Use .toarray() because t-SNE doesn't like sparse matrices
    tsne = TSNE(n_components=2, random_state=42, perplexity=min(5, len(videos) - 1))
    coords = tsne.fit_transform(X.toarray())
    
    # Build data for Chart.js scatter plot
    plot_data = []
    for i, video in enumerate(videos):
        label_index = int(labels[i])
        plot_data.append({
            "x": float(coords[i, 0]),
            "y": float(coords[i, 1]),
            "label": cluster_name_map.get(label_index, "Other"),
            "title": video["title"] # For the tooltip
        })
    
    # Return all results in a dictionary
    return {
        "labels": list(map(int, labels)),
        "cluster_name_map": cluster_name_map,
        "plot_data": plot_data,
        "top_keywords": top_keywords
    }
