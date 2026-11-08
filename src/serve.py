NEAR_X = 1500  # правее — подающий с ближней стороны (стоит справа за кадром)


def serve_side(start, end, xs, visible, near_x=NEAR_X) -> str:
    """Сторона подачи по первой точке мяча в отрезке [start, end].
    Вернуть 'near', 'far' или 'unknown', если мяч в отрезке не виден."""
    for i in range(start, end + 1, 1):
        if visible[i] == 1:
            return 'near' if xs[i] > near_x else 'far'
    return 'unknown'