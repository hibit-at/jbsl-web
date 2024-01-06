import os

import django

division_colors = {
    0: (0, 0, 0, 255),  # 黒
    1: (200, 50, 200, 255),  # 紫
    2: (255, 128, 50, 255),  # 赤
    3: (200, 200, 0, 255),  # 黄
    4: (50, 50, 200, 255),  # 青
    # 他のdivisionに対しても色を追加できます
}

division_colors_transparent = {
    0: "rgba(0, 0, 0, 255)",  # 黒
    1: "rgba(220,130,250,.8)",  # 紫
    2: "rgba(255,128,128,.8)",  # 赤
    3: "rgba(255,255,128,.8)",  # 黄
    4: "rgba(130,211,255,.8)",  # 青
    # 他のdivisionに対しても色を追加できます
}

division_borders = {
    0: 2000,
    1: 2000,
    2: 1150,
    3: 975,
    4: 800,
}


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()


def get_division(nps):
    if nps > 8:
        return 1
    elif nps > 6:
        return 2
    elif nps > 4:
        return 3
    else:
        return 4
