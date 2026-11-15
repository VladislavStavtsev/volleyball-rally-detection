import pandas as pd
import math


FPS = 29.97

NET_LEFT = (542, 382)
NET_RIGHT = (1407, 385)

def remove_jumps(visible, xs, ys, max_jump=150):
    """Убрать одиночные скачки детектора: точку, которая отскочила
    больше чем на max_jump пикс/кадр и от предыдущей, и от следующей видимой."""
    clean = visible.copy()
    idx = [i for i, v in enumerate(visible) if v == 1]
    for a, b, c in zip(idx, idx[1:], idx[2:]):
        to_prev = math.dist((xs[a], ys[a]), (xs[b], ys[b])) / (b - a)
        to_next = math.dist((xs[b], ys[b]), (xs[c], ys[c])) / (c - b)
        if to_prev > max_jump and to_next > max_jump:
            clean[b] = 0
    return clean

def net_y(x: float) -> float:
    """Y верхнего края сетки в точке x (прямая через две измеренные точки)."""
    (x1, y1), (x2, y2) = NET_LEFT, NET_RIGHT
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

def fill_gaps(visible: list[int], max_gap: int) -> list[int]:
    """Залить нулями-дыры длиной <= max_gap, если слева и справа от них единицы."""
    result = visible.copy()
    last_one = None

    for i in range(len(visible)):
        if visible[i] == 1:
            if last_one is not None:
                gap = i - last_one - 1
                if 0 < gap <= max_gap:
                    result[last_one + 1 : i] = [1] * gap
            last_one = i
    return result                    


def find_segments(visible: list[int]) -> list[tuple[int, int]]:
    """Найти отрезки подряд идущих единиц. Вернуть [(start_frame, end_frame), ...] включительно."""
    result = []
    slow = fast = 0
    while fast < len(visible):
        while fast < len(visible) and visible[fast] == 0:
            fast += 1

        slow = fast
        while fast < len(visible) and visible[fast] != 0:
            fast += 1
        if slow < fast:
            result.append((slow, fast - 1))    

    return result    


def merge_segments(segments: list[tuple[int, int]], merge_window: int) -> list[tuple[int, int]]:
    """Объединить соседние отрезки, если между концом одного и началом следующего <= merge_window кадров."""
    if not segments:
        return []

    result = [segments[0]]
    for start, end in segments[1:]:
        last_start, last_end = result[-1]
        gap = start - last_end - 1
        if gap <= merge_window:
            result[-1] = (last_start, end)
        else:
            result.append((start, end))
    return result


def filter_short(segments: list[tuple[int, int]], min_len: int) -> list[tuple[int, int]]:
    """Оставить отрезки длиной >= min_len кадров."""
    result = []
    for start, end in segments:
        if end - start + 1 >= min_len:
            result.append((start, end))
    return result    

def is_above_net(x: float, y: float) -> bool:
    """Мяч выше верхнего края сетки (Y растёт вниз, поэтому 'меньше' = 'выше')."""
    return y < net_y(x)


def filter_below_net(segments, xs, ys, visible) -> list[tuple[int, int]]:
    """Оставить отрезки, где мяч хотя бы раз был выше верхнего края сетки."""
    result = []
    for start, end in segments:
        for i in range(start, end + 1):
            if visible[i] == 1 and is_above_net(xs[i], ys[i]):
                result.append((start, end))
                break
    return result

def find_bounce(ys, visible, start, end, dy=8, k=3):
    """Первый отскок в кадрах [start, end]: мяч шёл вниз и развернулся вверх.
    Y растёт вниз, поэтому отскок — это локальный максимум Y."""
    frames = [i for i in range(start, end + 1) if visible[i] == 1]
    for n in range(k, len(frames) - k):
        i = frames[n]
        went_down = ys[i] - ys[frames[n - k]] >= dy
        goes_up = ys[i] - ys[frames[n + k]] >= dy
        if went_down and goes_up:
            return i
    return None


def split_on_low_ball(segments, xs, ys, visible, max_low=60, tail=30):
    """Разрезать отрезки там, где мяч дольше max_low кадров не поднимается выше сетки.
    Конец каждого куска — отскок от пола, если он найден, иначе последний раз выше сетки + tail."""
    result = []
    for start, end in segments:
        above = [i for i in range(start, end + 1)
                 if visible[i] == 1 and is_above_net(xs[i], ys[i])]
        if not above:
            result.append((start, end))
            continue

        piece_start = start
        prev = above[0]
        for i in above[1:] + [None]:
            if i is not None and i - prev <= max_low:
                prev = i
                continue
            low_end = end if i is None else i - 1
            bounce = find_bounce(ys, visible, prev, low_end)
            piece_end = bounce if bounce is not None else min(low_end, prev + tail)
            result.append((piece_start, piece_end))
            if i is not None:
                piece_start = prev = i
    return result

def segment_rallies(visible, xs, ys, max_gap=10, merge_window=30,
                    min_len=90, max_low=45, tail=10, end_shift=30):
    visible = remove_jumps(visible, xs, ys)
    filled = fill_gaps(visible, max_gap)
    segments = find_segments(filled)
    merged = merge_segments(segments, merge_window)
    above_net = filter_below_net(merged, xs, ys, visible)
    pieces = split_on_low_ball(above_net, xs, ys, visible, max_low, tail)
    long_enough = filter_short(pieces, min_len)
    return [(s, max(s, e - end_shift)) for s, e in long_enough]


if __name__ == "__main__":
    df = pd.read_csv("outputs/match/ball.csv")
    rallies = segment_rallies(
        df["Visibility"].tolist(), df["X"].tolist(), df["Y"].tolist()
    )
    print(f"Найдено розыгрышей: {len(rallies)}")
    for i, (s, e) in enumerate(rallies, 1):
        print(f"{i:3d}  {s / FPS:7.1f} - {e / FPS:7.1f} с  ({(e - s + 1) / FPS:.1f} с)")