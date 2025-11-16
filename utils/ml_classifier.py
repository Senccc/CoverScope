# utils/ml_classifier.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
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

    return list(map(int, labels)), cluster_name_map
