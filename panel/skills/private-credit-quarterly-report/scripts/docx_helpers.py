"""python-docx builders matching the Junson Private Credit Quarterly template.

Usage:
    from docx_helpers import *
    doc = new_report_doc("2026Q4", "13 Nov, 2026")
    section_heading(doc, "Market Size")
    subheading(doc, "Private credit market size")
    body(doc, [("Global private debt AUM has reached approximately ", False),
               ("US$2,600bn", True), (", of which ...", False)])
    exhibit(doc, "Exhibit 1: Private debt AUM (US$bn) by channel, 2015–2026",
            "charts/ex1.png", width_cm=16.5,
            note="Note: ...  Source: PitchBook.")
    exhibit_pair(doc,
        ("Exhibit 3: ...", "charts/ex3.png", "Note: ...  Source: PitchBook."),
        ("Exhibit 4: ...", "charts/ex4.png", "Note: ...  Source: PitchBook."))
    t = data_table(doc, header=["Metric", "PD (All)", "HY"],
                   rows=[["Annualised return", "7.8%", "5.3%"]])
    doc.save("out.docx")

All formatting constants mirror references/style-guide.md and the example docx.

三处相对基线成稿的修正（基线那份确实有这三个问题，实测）：
  1. exhibit()/exhibit_pair() 断言插入宽 ≤ 17.12cm —— 基线有两张 17.53cm 溢出页面
  2. data_table() 表头行加 <w:tblHeader/> —— 基线 36 张表只有 12 张有
  3. 新增 hyperlink()，并强制完整 URL —— 基线 0 个超链接
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# 文档色全部从 palette 取 —— 一个 hex 都不在本文件写死。
# 2026-08-24 之前这里写死了四个 RGBColor，全是同事 v2 的旧值
# （NAVY 1F3864 / BLUE 2E74B5 / BODY_C 222A35 / GRAY 7F8B99），
# 而 palette 早就换成 OTF 色了 —— 只改 GRID_HEX/NAVY_HEX 不够，正文色也一直是深灰蓝而非纯黑。
from palette import DOCX as _DOCX, DOCX_TEXT as _T


def _rgb(hexstr):
    h = hexstr.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


NAVY   = _rgb(_T["navy"])      # #16283F 标题 / 小节 / 题注 / 页眉线
BLUE   = _rgb(_T["accent"])    # #2E6DA4 "Research" / 二级小节
BODY_C = _rgb(_T["body"])      # #000000 正文，纯黑
GRAY_META = _rgb(_T["meta"])   # #8C97A5 季度标签 / 覆盖行 / 页眉页脚
GRAY_NOTE = _rgb(_T["note"])   # #5A6B7B 图下 Note / Source
GRAY = GRAY_NOTE               # 旧名兼容：默认指图注灰
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRID_HEX = _DOCX["grid"]        # C9D2DC 表格框线
NAVY_HEX = _DOCX["header_fill"] # 1F3B5B 表头填充

# 页面 A4、左右边距各 1.94cm → 正文可用宽 17.12cm。
# 基线成稿里有两张图插到 17.53cm，溢出 0.41cm —— 所以这里设硬上限。
USABLE_CM = 17.12
PAIR_CM = 8.51          # 并排单张（8.51×2 + 0.1 gap ≈ 17.12）
SOLO_CM = 17.12         # 单图满宽 = 正文可用宽
TALL_CM = 13.46         # 窄高单图（tall 画布 5.30 in），居中插入


# ---------------------------------------------------------------- low level
def _run(p, text, size=9.5, bold=False, color=BODY_C, italic=False):
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return r


def _spacing(p, after=6, before=0):
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)


def _set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_table_borders(table, color=GRID_HEX, none=False):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        if none:
            el.set(qn("w:val"), "none"); el.set(qn("w:sz"), "0")
            el.set(qn("w:space"), "0"); el.set(qn("w:color"), "FFFFFF")
        else:
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
            el.set(qn("w:space"), "0"); el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), "10"); el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


# ---------------------------------------------------------------- document
def new_report_doc(quarter, date_str, title="Private Credit Quarterly Report",
                   coverage="Coverage: private credit / direct lending / BDC / MM CLO"):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.94)
    sec.top_margin = sec.bottom_margin = Cm(1.59)

    # default font
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(9.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "DengXian")

    # title block
    p = doc.add_paragraph(); _spacing(p, after=0)
    _run(p, "JUNSON Capital ", 26, True, NAVY)
    _run(p, "Research", 26, False, BLUE)
    p = doc.add_paragraph(); _spacing(p, after=2)
    _run(p, title, 20, False, NAVY)
    _run(p, f"  ({quarter})", 13, False, GRAY_META)
    p = doc.add_paragraph(); _spacing(p, after=8)
    _run(p, coverage, 8.5, False, GRAY_META)
    tab = p.paragraph_format.tab_stops.add_tab_stop(Cm(17.1), WD_TAB_ALIGNMENT.RIGHT)
    _run(p, "\t" + date_str, 8.5, False, BODY_C)
    _bottom_rule(p)

    # header / footer
    hp = sec.header.paragraphs[0]
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(17.1), WD_TAB_ALIGNMENT.RIGHT)
    _run(hp, "JUNSON Capital｜ Private Credit Quarterly", 8.5, False, GRAY_META)
    _run(hp, f"\t{quarter}", 8.5, False, GRAY_META)
    _bottom_rule(hp, color=NAVY_HEX)
    fp = sec.footer.paragraphs[0]
    _run(fp, "Fundamental Analysis Report — For internal research use only",
         8.5, False, GRAY_META)
    return doc


def _bottom_rule(p, color=NAVY_HEX, sz="6"):
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), sz)
    bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    pPr.append(pbdr)


# ---------------------------------------------------------------- text blocks
def section_heading(doc, text):
    p = doc.add_paragraph(); _spacing(p, after=4, before=10)
    _run(p, text, 18, True, NAVY)
    return p


def subheading(doc, text):
    p = doc.add_paragraph(); _spacing(p, after=3, before=6)
    _run(p, text, 12.5, True, BLUE)
    return p


def minorheading(doc, text):
    """三级小标题（§8 的 Fund snapshot / Portfolio composition / Fund level
    performance detail）。比 subheading 小一档、深藏蓝，不占编号。

    ⛔ Alex 2026-08-25：「Fund Update 其中有三个 fund，每个 fund 下面的结构都要是一样的，
       要包含 Fund snapshot、Portfolio composition、Fund level performance detail」——
       这三段名必须**印在纸上**，不是只在 spec 里写着。
    """
    p = doc.add_paragraph(); _spacing(p, after=2, before=6)
    _run(p, text, 10, True, NAVY)
    return p


def plain_table(doc, label, header, rows, note=None, **kw):
    """**不带 Exhibit 编号**的小表 —— §8 的 Fund snapshot 两张表用这个。

    它们不是 exhibit（不在 exhibit_manifest.json 里、不参与 1–58 的编号），
    所以走这条路：一行加粗小标签 + 表 +（可选）Note，编号自查不会把它算进去。
    """
    if label:
        p = doc.add_paragraph(); _spacing(p, after=1, before=4)
        _run(p, label, 8.5, True, NAVY)
    t = data_table(doc, header, rows, **kw)
    if note:
        _note(doc, note)
    return t


def body(doc, parts, after=6):
    """parts: str, or list of (text, bold) tuples for inline bold numbers."""
    p = doc.add_paragraph(); _spacing(p, after=after)
    if isinstance(parts, str):
        parts = [(parts, False)]
    for text, bold in parts:
        _run(p, text, 9.5, bold, BODY_C)
    return p


def bullet(doc, parts, after=4):
    """List Paragraph bullet; parts as in body(). Lead-in phrase usually bold."""
    p = doc.add_paragraph(style="List Paragraph"); _spacing(p, after=after)
    p.paragraph_format.left_indent = Cm(0.63)
    # manual bullet char (template uses list numbering; a literal bullet renders same)
    if isinstance(parts, str):
        parts = [(parts, False)]
    _run(p, "· ", 9.5, True, BODY_C)
    for text, bold in parts:
        _run(p, text, 9.5, bold, BODY_C)
    return p


# ---------------------------------------------------------------- exhibits
def _caption(container, text):
    p = container.add_paragraph(); _spacing(p, after=2, before=4)
    _run(p, text, 8.5, True, NAVY)
    return p


def _note(container, text):
    p = container.add_paragraph(); _spacing(p, after=8)
    _run(p, text, 7, False, GRAY)
    return p


def _assert_width(width_cm, image_path):
    if width_cm > USABLE_CM + 0.01:
        raise SystemExit(
            f"[版面] {image_path}: 插入宽 {width_cm}cm 超出正文可用宽 {USABLE_CM}cm，会溢出页面。\n"
            f"  单图上限 {SOLO_CM}cm，并排单张 {PAIR_CM}cm。"
            f"（基线成稿里那两张 17.53cm 的图就是这么溢出的。）")


def exhibit(doc, caption, image_path, width_cm=SOLO_CM, note=None):
    _assert_width(width_cm, image_path)
    """Full-width exhibit: caption -> image -> note. 窄于满宽的图居中插入。"""
    _caption(doc, caption)
    p = doc.add_paragraph(); _spacing(p, after=2)
    if width_cm < SOLO_CM - 0.1:
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(image_path, width=Cm(width_cm))
    if note:
        _note(doc, note)


def exhibit_pair(doc, left, right, img_width_cm=PAIR_CM):
    """Side-by-side exhibits. left/right = (caption, image_path, note)."""
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(t, none=True)
    t.columns[0].width = Cm(8.7); t.columns[1].width = Cm(8.7)
    for cell, (caption, img, note) in zip(t.rows[0].cells, (left, right)):
        cell._tc.get_or_add_tcPr()
        first = cell.paragraphs[0]
        _run(first, caption, 8.5, True, NAVY); _spacing(first, after=2)
        if img:
            p = cell.add_paragraph(); _spacing(p, after=2)
            p.add_run().add_picture(img, width=Cm(img_width_cm))
        if note:
            np_ = cell.add_paragraph(); _spacing(np_, after=6)
            _run(np_, note, 7, False, GRAY)
    return t


def table_pair(doc, left, right, gap_cm=0.4):
    """两张表**横向并排**（无框线 1×2 外层表，左右各嵌一张）。

    ⛔ Alex 2026-08-26：「fund snapshot 格式全错，你没有仔细看同事的报告，格式必须锁死固定，
       是两个分开的的横向排放的表，表头和最左侧边的栏必须一样。除了季度。我跟你说过啊」
    同事那版 §8 每只基金的 Fund snapshot 就是**外层 1×2**：
      左格 = 静态事实表（**没有表头行**，纯 label|value）
      右格 = `Metric | <pq> | <cq> | QoQ Δ`（有深蓝表头行）
    我上一版把两张表上下摞着放、还给左表加了个 `Metric | Value` 的深蓝表头 —— 两处都错。

    left / right = (header_or_None, rows, col_widths_cm)。header 传 None 就不画表头行。
    """
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(t, none=True)
    half = (SOLO_CM - gap_cm) / 2
    t.columns[0].width = Cm(half); t.columns[1].width = Cm(half)
    for cell, spec in zip(t.rows[0].cells, (left, right)):
        cell._tc.get_or_add_tcPr()
        hdr, rows, widths = spec
        # 外层格的第一个空段落会撑出一行空白 —— 把表塞进去之后删掉它
        _ph = cell.paragraphs[0]
        _inner = data_table(cell, hdr, rows, col_widths_cm=widths,
                            bold_first_col=True, fixed_cols=bool(widths),
                            no_header=hdr is None, zebra=ZEBRA_HEX,
                            first_col_fill=(FIRSTCOL_HEX if hdr is None else None))
        _ph._p.getparent().remove(_ph._p)
    return t


def exhibit_with_panel(doc, caption, image_path, panel_title, bullets,
                       note=None, img_width_cm=PAIR_CM):
    """图 + 侧栏文字，无框线 1×2 表格。

    基线成稿的 Exhibit 31 就是这个排法：左格是图，右格是一个带小标题的要点栏。
    bullets 是纯文本列表（每条一段），出处写在 exhibit 的 Note 里。
    """
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(t, none=True)
    t.columns[0].width = Cm(8.7); t.columns[1].width = Cm(8.7)
    lc, rc = t.rows[0].cells
    lc._tc.get_or_add_tcPr(); rc._tc.get_or_add_tcPr()
    first = lc.paragraphs[0]
    _run(first, caption, 8.5, True, NAVY); _spacing(first, after=2)
    p = lc.add_paragraph(); _spacing(p, after=2)
    p.add_run().add_picture(image_path, width=Cm(img_width_cm))
    if note:
        np_ = lc.add_paragraph(); _spacing(np_, after=6)
        _run(np_, note, 7, False, GRAY)
    tp = rc.paragraphs[0]
    _run(tp, panel_title, 8.5, True, NAVY); _spacing(tp, after=3)
    for bt in bullets:
        bp = rc.add_paragraph(); _spacing(bp, after=4)
        _run(bp, '\u00b7 ' + bt, 7.5, False, BODY_C)
    return t


GROUP_ROW_HEX = "E8E8E8"      # 分组标题行的灰底（同事那版 E48 用的就是这个）
# Fund snapshot 的两抹底色 —— Alex 2026-08-26：「fund snapshot 的表格里面是有颜色的」。
# 同事那版：左表首列 EAF0F7 + 深蓝字，值列 FFFFFF/F7F9FB 隔行；右表深蓝表头 + 同样隔行。
# 我们用 house 调色板里同位的两个色，跟报告里其他 18 张表保持一致。
FIRSTCOL_HEX = _DOCX["firstcol_fill"]      # EEF2F6
ZEBRA_HEX = "F2F5F9"


def _fix_table_layout(t, col_widths_cm):
    """把表格切成**固定列宽**：写 tblLayout=fixed + tblW + tblGrid，并逐格设宽。

    ⛔ 只设 `cell.width` 是没用的 —— python-docx 建出来的表默认 autofit，Word 打开后
    按内容重算列宽，声明的宽度只当建议。E48 第一列声明 4.5cm、实测最长的
    "HarbourVest Direct Lending Fund II" 只要 4.15cm，本该一行放得下，可纸上还是折成
    两行 —— 就是被 autofit 把宽度分给了 "Dry powder %" / "PB quartile" 那几列
    （Alex 2026-08-26 看到的）。fixed 之后声明多少就是多少。
    """
    tw = [int(round(w * 567)) for w in col_widths_cm]      # cm -> twip（1cm = 567 twip）
    tblPr = t._tbl.tblPr
    for tag in ('w:tblLayout', 'w:tblW'):
        for el in tblPr.findall(qn(tag)):
            tblPr.remove(el)
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    wEl = OxmlElement('w:tblW')
    wEl.set(qn('w:type'), 'dxa'); wEl.set(qn('w:w'), str(sum(tw))); tblPr.append(wEl)
    grid = t._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        t._tbl.remove(grid)
    grid = OxmlElement('w:tblGrid')
    for w in tw:
        gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), str(w)); grid.append(gc)
    t._tbl.insert(list(t._tbl).index(tblPr) + 1, grid)
    t.autofit = False
    for row in t.rows:
        for i, w in enumerate(tw):
            if i < len(row.cells):
                row.cells[i].width = Twips(w)


def data_table(doc, header, rows, col_widths_cm=None, first_col_left=True,
               bold_first_col=False, size=7.5, group_rows=None, zebra=None,
               fixed_cols=False, no_header=False, first_col_fill=None):
    """Navy-header data table matching the template.

    group_rows: 一组行号（**body 行的 0-based 序号**），这些行画成**分组标题行**：
        整行灰底 E8E8E8、首格加粗、其余格留空并横向合并。
        ⛔ Alex 2026-08-25：E48 要加 `Core-to-upper MM` / `Low-to-core MM` 两行分组标题，
        「背景是灰色的」—— 同事那版就是这么做的（r4 / r8，底色 E8E8E8）。
    zebra: 隔行浅底色。⛔ Alex 2026-08-26：「报告中所有出现的表格的背景，都需要像
        Fund snapshot 的表格背景一样 一条白 一条灰。不包含表头，仅限表格内容部分。」
        所以这是**房子默认**：`zebra=None` 用默认色 ZEBRA_HEX，要关掉必须显式传
        `zebra=False`。原来默认是关的，只有 Fund snapshot 两张显式打开。
    """
    if zebra is None:
        zebra = ZEBRA_HEX
    group_rows = set(group_rows or ())
    # no_header：不画深蓝表头行。§8 Fund snapshot 的左表就是这样（同事那版没有表头）。
    if no_header:
        ncol = max(len(r) for r in rows)
        t = doc.add_table(rows=len(rows), cols=ncol)
        _set_table_borders(t)
        if col_widths_cm:
            if fixed_cols:
                _fix_table_layout(t, col_widths_cm)
            else:
                for i, w in enumerate(col_widths_cm):
                    for row in t.rows:
                        row.cells[i].width = Cm(w)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                c = t.rows[i].cells[j]
                # 首列底色 + 深蓝字；其余列隔行浅底 —— 同事那版 Fund snapshot 左表
                # 就是 EAF0F7 首列 + FFFFFF/F7F9FB 隔行（Alex 2026-08-26：
                # 「fund snapshot 的表格里面是有颜色的」）。我们用自己那套同名色。
                if j == 0 and first_col_fill:
                    _set_cell_bg(c, first_col_fill)
                elif zebra and i % 2 == 1:
                    _set_cell_bg(c, zebra)
                pp = c.paragraphs[0]; _spacing(pp, after=1)
                pp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                _run(pp, str(val), size, bold_first_col and j == 0,
                     NAVY if (j == 0 and first_col_fill) else BODY_C)
        return t
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    _set_table_borders(t)
    if col_widths_cm:
        if fixed_cols:
            # ⛔ 声明的列宽要真的生效必须走 fixed 布局，见 _fix_table_layout 的注释。
            #    E48 靠这个保证第一列每一行都只占一行。
            _fix_table_layout(t, col_widths_cm)
        else:
            for i, w in enumerate(col_widths_cm):
                for row in t.rows:
                    row.cells[i].width = Cm(w)
    # 表头行跨页重复：基线成稿 36 张表只有 12 张有，剩下 24 张跨页后看不到列名
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true")
    trPr.append(th)
    # header row
    for j, htext in enumerate(header):
        c = t.rows[0].cells[j]
        _set_cell_bg(c, NAVY_HEX)
        p = c.paragraphs[0]; _spacing(p, after=1)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, str(htext), size, True, WHITE)
    # body rows
    _z = 0
    for i, row in enumerate(rows, start=1):
        is_grp = (i - 1) in group_rows
        if not is_grp:
            _z += 1
        for j, val in enumerate(row):
            c = t.rows[i].cells[j]
            if is_grp:
                _set_cell_bg(c, GROUP_ROW_HEX)
            elif j == 0 and first_col_fill:
                _set_cell_bg(c, first_col_fill)
            elif zebra and _z % 2 == 0:
                _set_cell_bg(c, zebra)
            p = c.paragraphs[0]; _spacing(p, after=1)
            left = first_col_left and j == 0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if left else WD_ALIGN_PARAGRAPH.CENTER
            _run(p, str(val), size, (bold_first_col and j == 0) or (is_grp and j == 0), BODY_C)
        # ⛔ 分组标题行**不合并单元格**。
        #   合并过一版（2026-08-25），python-docx 合并时会把 9 个格子的段落全部搬进合并后的
        #   那一格 —— 于是那一格有 1 个带字的段落 + 8 个空段落，整行变成 9 行高，
        #   灰底拉出一大块空白（Alex 看到的就是这个）。
        #   同事那版本来也没合并：9 个格子各自留空、整行统一灰底、标题在第一格。照他的做。
    return t


def exhibit_table(doc, caption, header, rows, note=None, **kw):
    """Caption -> data table -> note."""
    _caption(doc, caption)
    t = data_table(doc, header, rows, **kw)
    if note:
        _note(doc, note)
    return t


def hyperlink(paragraph, url, text=None, size=7.0, color=BLUE):
    """在段落里插一个真超链接。

    Related news 每条的来源必须用这个 —— 而且 url 必须是**那一篇文章的完整网址**，
    只到域名（bain.com、bloomberg.com）不算，读者点进去落到首页找不到原文。
    拿不到准确网址的新闻就不要写这一条。
    """
    import re as _re
    m = _re.match(r"https?://[^/]+(/?.*)$", url or "")
    if not m or m.group(1).strip("/") == "":
        raise SystemExit(
            f"[来源] 超链接 {url!r} 只到域名，没到文章。\n"
            f"  必须是那一篇的完整 URL（带路径）；拿不到就删掉这条新闻，不要用域名凑。")
    part = paragraph.part
    r_id = part.relate_to(
        url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    run = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    for tag, val in (("w:color", f"{color.__str__()}"), ):
        el = OxmlElement(tag); el.set(qn("w:val"), val); rPr.append(el)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rPr.append(u)
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2))); rPr.append(sz)
    run.append(rPr)
    t = OxmlElement("w:t"); t.text = text or url
    run.append(t); h.append(run)
    paragraph._p.append(h)
    return paragraph


def disclaimer(doc, text):
    p = doc.add_paragraph(); _spacing(p, before=12)
    _run(p, text, 7, False, GRAY)
    return p
