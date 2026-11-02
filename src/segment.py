import pandas as pd

FPS = 29.97


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


def segment_rallies(visible, max_gap=10, merge_window=30, min_len=60):
    filled = fill_gaps(visible, max_gap)
    segments = find_segments(filled)
    merged = merge_segments(segments, merge_window)
    return filter_short(merged, min_len)


if __name__ == "__main__":
    df = pd.read_csv("outputs/match/ball.csv")
    rallies = segment_rallies(df["Visibility"].tolist())
    print(f"Найдено розыгрышей: {len(rallies)}")
    for i, (s, e) in enumerate(rallies, 1):
        print(f"{i:3d}  {s / FPS:7.1f} - {e / FPS:7.1f} с  ({(e - s + 1) / FPS:.1f} с)")