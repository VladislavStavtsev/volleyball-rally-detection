import pandas as pd

from src.segment import FPS, segment_rallies
from src.segment import FPS, remove_jumps, segment_rallies
from src.serve import serve_side


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

def match_events(labels, preds, start_tol=1.0) -> list[tuple[int, int]]:
    """Сопоставление по событию: предсказание пересекается с розыгрышем
    и его начало отличается не больше чем на start_tol секунд."""
    used = set()
    pairs = []
    for i, (ls, le) in enumerate(labels):
        best_j, best_diff = None, None
        for j, (ps, pe) in enumerate(preds):
            if j in used or iou((ls, le), (ps, pe)) == 0:
                continue
            diff = abs(ps - ls)
            if diff <= start_tol and (best_diff is None or diff < best_diff):
                best_j, best_diff = j, diff
        if best_j is not None:
            used.add(best_j)
            pairs.append((i, best_j))
    return pairs


def boundary_errors(labels, preds, pairs) -> dict:
    """Ошибки границ по найденным парам, в секундах.
    Сдвиг конца со знаком: плюс — программа заканчивает позже разметки."""
    if not pairs:
        return {}
    d_start = [preds[j][0] - labels[i][0] for i, j in pairs]
    d_end = [preds[j][1] - labels[i][1] for i, j in pairs]
    n = len(pairs)
    return {
        "start_mae": round(sum(abs(d) for d in d_start) / n, 2),
        "end_mae": round(sum(abs(d) for d in d_end) / n, 2),
        "end_bias": round(sum(d_end) / n, 2),
    }

if __name__ == "__main__":
    labels_df = pd.read_csv("labels/labels.csv")
    labels = list(zip(labels_df["start"], labels_df["end"]))

    ball = pd.read_csv("outputs/match/ball.csv")
    frames = segment_rallies(ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist())
    preds = [(s / FPS, e / FPS) for s, e in frames]

    strict = match(labels, preds)
    events = match_events(labels, preds)

    print("Строго (IoU >= 0.5):  ", metrics(len(labels), len(preds), len(strict)))
    print("По событию (старт ±1 с):", metrics(len(labels), len(preds), len(events)))
    print("Ошибки границ:          ", boundary_errors(labels, preds, events))

    print("\nПропущенные по событию:")
    found = {i for i, _ in events}
    for i, (ls, le) in enumerate(labels):
        if i not in found:
            print(f"#{i + 1:2d}  {int(ls) // 60}:{int(ls) % 60:02d}  ({ls:.0f}-{le:.0f})")

    visible = remove_jumps(ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist())
    xs = ball["X"].tolist()
    true_sides = labels_df["serve_side"].tolist()

    print("\nСторона подачи (по найденным розыгрышам):")
    for half_name, first_half in [("1-я половина", True), ("2-я половина", False)]:
        correct = total = 0
        for i, j in events:
            if (labels[i][0] < 638) != first_half:
                continue
            s, e = frames[j]
            total += 1
            correct += serve_side(s, e, xs, visible) == true_sides[i]
        print(f"{half_name}: {correct}/{total} = {correct / total:.2f}")

    print("\nОшибки стороны подачи:")
    for i, j in events:
        s, e = frames[j]
        pred_side = serve_side(s, e, xs, visible)
        if pred_side != true_sides[i]:
            print(f"#{i + 1:2d}  {int(labels[i][0]) // 60}:{int(labels[i][0]) % 60:02d}  "
                  f"разметка {true_sides[i]}, предсказано {pred_side}")        