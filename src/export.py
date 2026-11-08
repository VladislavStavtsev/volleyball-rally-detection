import argparse
import json

import pandas as pd

from src.segment import segment_rallies
from src.segment import remove_jumps, segment_rallies
from src.serve import serve_side

def build_rallies(frames, fps, xs, visible):
    """Отрезки в кадрах → розыгрыши в формате задания (+ поля для БД)."""
    return [
        {
            "number": n,
            "start": round(s / fps, 1),
            "end": round(e / fps, 1),
            "start_frame": s,
            "end_frame": e,
            "serve_side": serve_side(s, e, xs, visible),
        }
        for n, (s, e) in enumerate(frames, 1)
    ]


def main():
    parser = argparse.ArgumentParser(description="ball.csv → rallies.json")
    parser.add_argument("--csv", required=True, help="путь к ball.csv от трекера")
    parser.add_argument("--out", required=True, help="куда сохранить JSON")
    parser.add_argument("--fps", type=float, default=29.97, help="FPS видео")
    args = parser.parse_args()

    ball = pd.read_csv(args.csv)
    frames = segment_rallies(ball["Visibility"].tolist(), ball["X"].tolist(), ball["Y"].tolist())
    xs = ball["X"].tolist()
    visible = remove_jumps(ball["Visibility"].tolist(), xs, ball["Y"].tolist())
    rallies = build_rallies(frames, args.fps, xs, visible)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"fps": args.fps, "rallies": rallies}, f, ensure_ascii=False, indent=2)
    print(f"Сохранено {len(rallies)} розыгрышей в {args.out}")


if __name__ == "__main__":
    main()