"""表格出图层 —— 把表渲染成与报告 Word 表格同款的 PNG。
样式冻结，定稿后不许改。用 Chromium 截图，不用 matplotlib（文本度量不可控）。
"""
import json, asyncio, html as _h
from pathlib import Path

# ---- 报告表格的真实样式（从 OTF_2026Q2 报告的 document.xml 抠出来） ----
HDR_BG   = '#1F3B5B'   # 表头深蓝
HDR_FG   = '#FFFFFF'   # 表头白字
STUB_BG  = '#EEF2F6'   # 首列（行标）浅蓝灰底
BORDER   = '#C9D2DC'   # 全部框线，0.5pt
TEXT     = '#000000'   # 纯黑（原 #22303C 已作废）
NOTE     = '#5A6B7B'   # 表下灰色斜体小注
FONT     = "'Liberation Sans','Arial',sans-serif"   # 报告表格用 Arial

# ---- 尺寸：与图一样锁 1:1（画布宽 = Word 插入宽），字号 Arial 8pt ----
DPI        = 200                      # 与 chartlib.DPI 一致
SCALE      = 2                        # Chromium device_scale_factor
PX_PER_IN  = DPI / SCALE              # 1 CSS px = 1/100 in
TABLE_W_IN = 6.05                     # 与 chartlib.CANVAS_W 一致（正文宽的 85%）
WIDTH_PX   = round(TABLE_W_IN * PX_PER_IN)          # 605
FS_PT      = 8.0                                     # 所有表格统一 Arial 8 号
FS_PX      = round(FS_PT / 72 * PX_PER_IN, 2)        # 11.11 CSS px = 8pt

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#fff;font-family:%(font)s;color:%(text)s}
table{border-collapse:collapse;table-layout:fixed;width:%(w)dpx}
th,td{border:.5px solid %(border)s;padding:3.5px 5px;font-size:%(fs)spx;
      line-height:1.35;vertical-align:middle}
th{background:%(hdr_bg)s;color:%(hdr_fg)s;font-weight:700}
th.stub{text-align:left}
th.num{text-align:center}
td.stub{background:%(stub_bg)s;text-align:left}
td.num{text-align:center}
tr.total td{font-weight:700}
p.note{width:%(w)dpx;margin-top:6px;font-size:%(fs)spx;line-height:1.4;
       color:%(note)s;font-style:italic}
""" % dict(font=FONT, text=TEXT, border=BORDER, hdr_bg=HDR_BG, hdr_fg=HDR_FG,
           stub_bg=STUB_BG, note=NOTE, w=WIDTH_PX, fs=FS_PX)


def build_html(spec):
    """spec = {cols:[...], colw:[...], rows:[{cells:[...], total:bool}], note:str}"""
    e = _h.escape
    # colw 按比例归一到 WIDTH_PX —— 调用方给百分比或任意相对值都行
    _cw = spec['colw']; _tot = sum(_cw) or 1
    _cw = [round(w / _tot * WIDTH_PX) for w in _cw]
    _cw[-1] += WIDTH_PX - sum(_cw)          # 收尾差补到最后一列
    cg = ''.join(f'<col style="width:{w}px">' for w in _cw)
    head = '<tr>' + ''.join(
        f'<th class="{"stub" if i==0 else "num"}">{e(c)}</th>'
        for i, c in enumerate(spec['cols'])) + '</tr>'
    body = ''
    for r in spec['rows']:
        cls = ' class="total"' if r.get('total') else ''
        body += f'<tr{cls}>' + ''.join(
            f'<td class="{"stub" if i==0 else "num"}">{e(str(c))}</td>'
            for i, c in enumerate(r['cells'])) + '</tr>'
    note = f'<p class="note">{e(spec["note"])}</p>' if spec.get('note') else ''
    # 截图截 #wrap 而不是 body —— body 会跟着 viewport 撑宽，落盘就不是 1:1 了
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div id="wrap" style="width:{WIDTH_PX}px">'
            f'<table><colgroup>{cg}</colgroup>{head}{body}</table>{note}</div>')


def render(spec, out, scale=SCALE):
    from playwright.sync_api import sync_playwright
    Path('_t.html').write_text(build_html(spec), encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': WIDTH_PX + 40, 'height': 600},
                        device_scale_factor=scale)
        pg.goto('file://' + str(Path('_t.html').resolve()))
        pg.locator('#wrap').screenshot(path=out)
        b.close()
    Path('_t.html').unlink()
    # 与图同样的版面锁：落盘宽 ÷ DPI 必须等于插入宽，否则 1:1 破了
    try:
        from PIL import Image
        _w = Image.open(out).width / DPI
        if abs(_w - TABLE_W_IN) > 0.03:
            raise SystemExit(
                f'[版面] {out}: 落盘宽 {_w:.2f} in ≠ {TABLE_W_IN} in。'
                f'表格 PNG 也要 1:1，否则 Arial {FS_PT:g}pt 插进去就不是 {FS_PT:g}pt 了。')
    except ImportError:
        pass
    print('[written]', out, f'{TABLE_W_IN} in @ {DPI} dpi, Arial {FS_PT:g}pt')
