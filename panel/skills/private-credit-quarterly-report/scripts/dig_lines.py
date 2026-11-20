# -*- coding: utf-8 -*-
"""按颜色扫列，把折线图还原成数列。同色多条线时按上下顺序拆。"""
from PIL import Image
import numpy as np


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(int)


def cmask(a, c, tol=45):
    return ((np.abs(a[:, :, 0] - c[0]) < tol) &
            (np.abs(a[:, :, 1] - c[1]) < tol) &
            (np.abs(a[:, :, 2] - c[2]) < tol))


def runs(col_mask, min_gap=6):
    """一列里的连续像素段 -> [(y0,y1)]，段间隔 >= min_gap 才算两段。"""
    ys = np.nonzero(col_mask)[0]
    if not len(ys):
        return []
    out, s, p = [], ys[0], ys[0]
    for y in ys[1:]:
        if y - p >= min_gap:
            out.append((s, p)); s = y
        p = y
    out.append((s, p))
    return out


def scan(a, color, x0, x1, n, ytop, yval_top, ybot, yval_bot,
         band=None, nlines=1, tol=45, min_gap=6, halfwin=3):
    """x0..x1 均分 n 段（n+1 个点），每点取 ±halfwin 列的并集再拆段。
    返回 nlines 条序列（从上到下），缺测为 None。"""
    M = cmask(a, color, tol)
    if band:
        keep = np.zeros_like(M); keep[band[0]:band[1], :] = True; M = M & keep
    k = (yval_top - yval_bot) / (ytop - ybot)          # 每像素多少单位（负）
    out = [[] for _ in range(nlines)]
    diag = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        xi = int(round(x))
        col = M[:, max(0, xi - halfwin):xi + halfwin + 1].any(axis=1)
        rs = runs(col, min_gap)
        diag.append(len(rs))
        vals = [yval_bot + (ybot - (r0 + r1) / 2) * (-k) for r0, r1 in rs]
        vals = [yval_bot + ((r0 + r1) / 2 - ybot) * k for r0, r1 in rs]
        for j in range(nlines):
            out[j].append(round(vals[j], 3) if j < len(vals) else None)
    return out, diag
