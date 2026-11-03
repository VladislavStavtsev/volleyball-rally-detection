import pandas as pd

from src.segment import FPS, segment_rallies


def iou(a: tuple[float, float], b: tuple[float, float]) -> float:
    """IoU двух интервалов (start, end) в секундах."""
    start_a, end_a = a
    start_b, end_b = b
    start = max(start_a, start_b)
    end = min(end_a, end_b)
    intersection = max(0, end - start)
    union = max(end_a, end_b) - min(start_a, start_b)
    if union == 0:
        return 0.0
    return intersection / union 


def match(labels, preds, threshold=0.5) -> list[tuple[int, int]]:
    """Сопоставить разметку и предсказания. Вернуть пары индексов (i_label, j_pred)."""
    used = set()
    pairs = []
    for i, lab in enumerate(labels):
        best_j, best_iou = None, 0.0
        for j, pred in enumerate(preds):
            if j in used:
                continue
            score = iou(lab, pred)
            if score > best_iou:
                best_j, best_iou = j, score
        if best_j is not None and best_iou >= threshold:
            used.add(best_j)
            pairs.append((i, best_j))
    return pairs


def metrics(n_labels: int, n_preds: int, n_pairs: int) -> dict:
    """precision, recall, f1 по числу пар."""
    TP = n_pairs # найденные розыгрыши;
    FP = n_preds - n_pairs # ложные срабатывания;
    FN = n_labels - n_pairs # пропущенные;
    precision = TP / (TP + FP) if TP + FP > 0 else 0.0 # какая доля найденного правильная;
    recall = TP / (TP + FN) # какую долю настоящих нашли;
    f1 = 2 * precision * recall / (precision + recall)

    return {
    "tp": TP,
    "fp": FP,
    "fn": FN,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    }

if __name__ == "__main__":
    labels_df = pd.read_csv("labels/labels.csv")
    labels = list(zip(labels_df["start"], labels_df["end"]))

    ball = pd.read_csv("outputs/match/ball.csv")
    frames = segment_rallies(ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist())
    preds = [(s / FPS, e / FPS) for s, e in frames]

    pairs = match(labels, preds)
    print(metrics(len(labels), len(preds), len(pairs)))
    print("\nПропущенные розыгрыши и ближайшее предсказание:")
    matched = {i for i, _ in pairs}
    for i, lab in enumerate(labels):
        if i in matched:
            continue
        best = max(preds, key=lambda p: iou(lab, p))
        print(f"#{i + 1:2d}  разметка {lab[0]:6.0f}-{lab[1]:6.0f}   "
              f"ближайшее {best[0]:6.1f}-{best[1]:6.1f}   IoU {iou(lab, best):.2f}")