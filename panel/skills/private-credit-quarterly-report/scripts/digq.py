# -*- coding: utf-8 -*-
"""季度折线图的通用像素还原：颜色掩膜 + 轴刻度标签标定 + 等分 x。"""
from PIL import Image
import numpy as np


class Page:
    def __init__(self, path):
        self.a = np.asarray(Image.open(path).convert('RGB')).astype(int)
        self.chroma = (self.a.max(axis=2) - self.a.min(axis=2)) > 40

    def mask(self, c, tol=48, need_chroma=True):
        a = self.a
        m = ((np.abs(a[:, :, 0] - c[0]) < tol) &
             (np.abs(a[:, :, 1] - c[1]) < tol) &
             (np.abs(a[:, :, 2] - c[2]) < tol))
        return (m & self.chroma) if need_chroma else m

    def label_rows(self, x0, x1, y0, y1, minpx=2):
        """竖排刻度标签的行位置（用来标定 y 轴）。"""
        dark = (self.a[:, :, 0] < 115) & (self.a[:, :, 1] < 115) & (self.a[:, :, 2] < 115)
        rows = dark[y0:y1, x0:x1].sum(axis=1)
        ys = np.nonzero(rows > minpx)[0] + y0
        if not len(ys):
            return []
        out, s, p = [], ys[0], ys[0]
        for y in ys[1:]:
            if y - p > 4:
                out.append((s, p)); s = y
            p = y
        out.append((s, p))
        return [round((g[0] + g[1]) / 2, 1) for g in out]

    def xspan(self, m, ytop, ybot, x0, x1, minpx=1):
        cols = [x for x in range(x0, x1) if m[ytop:ybot, x].sum() >= minpx]
        return (cols[0], cols[-1]) if cols else None

    def series(self, m, ytop, ybot, xa, xb, n, y_at, val_at, hw=0):
        """xa..xb 等分 n-1 段取 n 个点；y_at/val_at 是标定的两点（像素行, 数值）。"""
        k = (val_at[1] - val_at[0]) / (y_at[1] - y_at[0])
        keep = np.zeros_like(m); keep[ytop:ybot, :] = True
        mm = m & keep
        out = []
        for i in range(n):
            xi = int(round(xa + (xb - xa) * i / (n - 1)))
            v = None
            for w in range(hw, hw + 4):
                ys = np.nonzero(mm[:, max(0, xi - w):xi + w + 1].any(axis=1))[0]
                if len(ys):
                    yc = (ys.min() + ys.max()) / 2
                    v = round(val_at[0] + (yc - y_at[0]) * k, 3)
                    break
            out.append(v)
        return out


def quarters(start_q, start_y, n):
    out, q, y = [], start_q, start_y
    for _ in range(n):
        out.append(f'{q}Q{str(y)[2:]}')
        q += 1
        if q == 5:
            q = 1; y += 1
    return out
