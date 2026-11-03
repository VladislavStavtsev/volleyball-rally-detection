import math

import pandas as pd

from src.evaluate import match
from src.segment import FPS, segment_rallies

ball = pd.read_csv("outputs/match/ball.csv")
visible, xs, ys = ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist()
labels_df = pd.read_csv("labels/labels.csv")
labels = list(zip(labels_df["start"], labels_df["end"]))

frames = segment_rallies(visible, xs, ys)
preds = [(s / FPS, e / FPS) for s, e in frames]
true_preds = {j for _, j in match(labels, preds)}


def max_start_speed(start, end, window=45, step=3):
    """Максимальный сдвиг мяча за step кадров в первые window кадров куска."""
    pts = [(i, xs[i], ys[i]) for i in range(start, min(end, start + window) + 1) if visible[i] == 1]
    best = 0.0
    for (i1, x1, y1), (i2, x2, y2) in zip(pts, pts[step:]):
        best = max(best, math.dist((x1, y1), (x2, y2)) / (i2 - i1))
    return best


rows = []
for j, (s, e) in enumerate(frames):
    rows.append({
        "tag": "TP" if j in true_preds else "FP",
        "time": f"{int(s / FPS) // 60}:{int(s / FPS) % 60:02d}",
        "speed": round(max_start_speed(s, e), 1),
    })

df = pd.DataFrame(rows).sort_values("speed")
print(df.to_string(index=False))
print(df.groupby("tag")["speed"].describe())