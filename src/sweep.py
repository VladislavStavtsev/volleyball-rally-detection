import itertools

import pandas as pd

from src.evaluate import match, metrics
from src.segment import FPS, segment_rallies

ball = pd.read_csv("outputs/match/ball.csv")
visible, xs, ys = ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist()
labels_df = pd.read_csv("labels/labels.csv")
labels = list(zip(labels_df["start"], labels_df["end"]))

grid = {
    "max_low": [30, 45, 60, 90],
    "tail": [0, 10, 20, 30],
    "min_len": [15, 30, 60],
}

rows = []
for max_low, tail, min_len in itertools.product(*grid.values()):
    frames = segment_rallies(visible, xs, ys, max_low=max_low, tail=tail, min_len=min_len)
    preds = [(s / FPS, e / FPS) for s, e in frames]
    m = metrics(len(labels), len(preds), len(match(labels, preds)))
    rows.append({"max_low": max_low, "tail": tail, "min_len": min_len, **m})

df = pd.DataFrame(rows).sort_values("f1", ascending=False)
print(df.head(10).to_string(index=False))
df.to_csv("outputs/sweep.csv", index=False)