import itertools

import pandas as pd

from src.evaluate import match, metrics
from src.segment import FPS, segment_rallies

ball = pd.read_csv("outputs/match/ball.csv")
visible, xs, ys = ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist()
labels_df = pd.read_csv("labels/labels.csv")
labels = list(zip(labels_df["start"], labels_df["end"]))

grid = {
    "max_low": [45],
    "tail": [10],
    "min_len": [60, 75, 90],
    "end_shift": [15, 30],
}

HALF = 638  # секунда, середина матча


def part(intervals, first_half):
    """Отрезки только из первой или только из второй половины, по началу."""
    return [iv for iv in intervals if (iv[0] < HALF) == first_half]


def score(labels, preds):
    return metrics(len(labels), len(preds), len(match(labels, preds)))


rows = []
for max_low, tail, min_len, end_shift in itertools.product(*grid.values()):
    frames = segment_rallies(visible, xs, ys, max_low=max_low, tail=tail,
                             min_len=min_len, end_shift=end_shift)
    preds = [(s / FPS, e / FPS) for s, e in frames]
    train = score(part(labels, True), part(preds, True))
    test = score(part(labels, False), part(preds, False))
    rows.append({"min_len": min_len, "end_shift": end_shift,
                 "train_f1": round(train["f1"], 3), "test_f1": round(test["f1"], 3)})

df = pd.DataFrame(rows).sort_values("train_f1", ascending=False)
print(df.to_string(index=False))