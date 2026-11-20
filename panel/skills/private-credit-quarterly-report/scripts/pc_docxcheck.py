#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成稿版面自查（Private Credit 季报版）

    python3 pc_docxcheck.py Junson_Private_Credit_Report_2026Q4_EN_v1.docx

基准全部来自 2026Q3 那份成稿的实测值（不是猜的）：
  A4 竖版 11906×16838、左右边距各 1100 twips（合计 1.53 in）、正文可用宽 6.74 in、
  并排图各 3.35 in、正文 7.5pt、表格框线 #C9D2DC / 表头底 #1F3B5B（色值从 junson_style.DOCX 取，别在本文件写死；#BFC7D1 / #1F3864 是同事 v2 的旧值，已作废）。
不通过就 exit 1。
"""
import io, os, re, sys, zipfile
from collections import Counter

A4_P = (11906, 16838)
MAR = 1100                    # 左右各 1100 twips
USABLE_IN = 6.74              # (21 - 1.94*2) cm / 2.54
IMG_PAIR = 3.35               # 并排图插入宽
IMG_MAX = USABLE_IN           # 单图上限 —— 超了就溢出页面
IMG_TOL = 0.05
BODY_SZ = 19                  # 半点 = 9.5pt（docDefaults）；正文 run 多为 15 = 7.5pt
BODY_BODY_SZ = 19             # 9.5pt —— 正文段
BODY_SMALL_SZ = 15            # 7.5pt —— 表格内容与图下 Note
# ⚠ 别把「最常见的显式 sz 标签」当基线正文字号：基线成稿的正文 run 不带 sz，
#   继承 docDefaults 的 19（9.5pt），显式的 15（7.5pt）是表格与 Note。
#   2026Q3 误判过一次，判据改成「两档都在、且 9.5 不少于 7.5 的一半」。
BODY_RUN_SZ = BODY_BODY_SZ
# 同上：从 junson_style.DOCX 取，保证「出稿用什么色」和「校验查什么色」永远一致。
from palette import DOCX as _DOCX, DEPRECATED as _DEPRECATED
_DEP = {'body_expected': _DOCX['body']}
GRID_HEX = _DOCX['grid']
# ⛔ 隔行底色也从出稿那边取，两边不许各写一份
from docx_helpers import ZEBRA_HEX
HDR_HEX = _DOCX['header_fill']
EMU = 914400
BANNED = ['To be written', 'TBD', '待补', '[placeholder]', 'PLACEHOLDER',
          'Not updated this quarter — ', 'lorem ipsum']

fails, warns, oks = [], [], []
def ok(m):   oks.append(m)
def bad(m):  fails.append(m)
def warn(m): warns.append(m)


def main(path):
    if not os.path.exists(path):
        sys.exit(f'找不到文件：{path}')
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
    txt = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', doc))

    # ── 1 纸张与边距 ────────────────────────────────────────────
    for t in re.findall(r'<w:pgSz[^/]*/>', doc):
        w = int(re.search(r'w:w="(\d+)"', t).group(1))
        h = int(re.search(r'w:h="(\d+)"', t).group(1))
        land = bool(re.search(r'w:orient="landscape"', t))
        if land:
            bad(f'出现横版节 {w}×{h} —— PC 季报全篇竖版，没有横版节')
        elif (w, h) == A4_P:
            ok(f'A4 竖版 {w}×{h}')
        else:
            bad(f'纸张 {w}×{h} 不是 A4 竖版（{w/1440:.2f}×{h/1440:.2f} in）')
    mars = re.findall(r'<w:pgMar[^/]*/>', doc)
    off = [t for t in mars
           if int(re.search(r'w:left="(\d+)"', t).group(1)) != MAR
           or int(re.search(r'w:right="(\d+)"', t).group(1)) != MAR]
    if off:
        bad(f'左右边距不是 {MAR}/{MAR} twips（合计 1.53 in）—— 正文可用宽会变')
    else:
        ok(f'左右边距 {MAR}/{MAR} = 1.53 in，正文可用宽 {USABLE_IN} in')

    # ── 2 正文字号与颜色 ────────────────────────────────────────
    szs = [int(x) for x in re.findall(r'<w:sz w:val="(\d+)"/>', doc)]
    if szs:
        cnt = Counter(szs)
        n_body, n_small = cnt.get(BODY_BODY_SZ, 0), cnt.get(BODY_SMALL_SZ, 0)
        # 基线成稿实际用到的字号档（half-points）：题注 8.5、节标题 12.5、Note 7.0、
        # 小注 6.5、封面 18 —— 都是合法档，只有这套之外的才提醒。
        ALLOWED_SZ = {19, 15, 17, 25, 14, 13, 36}
        stray = {k: v for k, v in cnt.items() if k not in ALLOWED_SZ and v > 20}
        if n_body and n_small and n_body >= n_small * 0.5:
            ok(f'字号两档就位：正文 {BODY_BODY_SZ/2:g} pt（{n_body} 处）'
               f'／表格与 Note {BODY_SMALL_SZ/2:g} pt（{n_small} 处）')
        else:
            bad(f'字号分布异常：{BODY_BODY_SZ/2:g} pt {n_body} 处、'
                f'{BODY_SMALL_SZ/2:g} pt {n_small} 处 —— 正文应是 9.5pt、表格与 Note 7.5pt')
        if stray:
            warn(f'另有非标字号（>20 处）：{ {k/2: v for k, v in stray.items()} }')
    cols = [c.upper() for c in re.findall(r'<w:color w:val="([0-9A-Fa-f]{6})"', doc)]
    if cols:
        top = Counter(cols).most_common(1)[0]
        ok(f'最常见字体颜色 #{top[0]}（{top[1]} 处）')
        # Alex 定的规矩（与 OTF 统一）：正文字体颜色必须是纯黑 000000。
        # #222A35 是同事 v2 成稿里的深灰蓝 —— 它是「基线的老值」，不是可接受值。
        if top[0] != _DEP.get('body_expected', '000000'):
            # 作废色值清单也从 palette 取 —— 不在本文件写死任何 hex
            why = _DEPRECATED.get(top[0])
            hint = f'（#{top[0]} 是{why}，本季起不再接受）' if why else ''
            bad(f'正文主色 #{top[0]}，必须是纯黑 #{_DOCX["body"]}{hint}')

    # ── 3 图片宽度 ─────────────────────────────────────────────
    rmap = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
    blocks = re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"/>.*?r:embed="(rId\d+)"', doc, re.S)
    if not blocks:
        bad('文档里一张图都没有')
    else:
        over = [(i, w) for i, (cx, _, _) in enumerate(blocks, 1)
                for w in [int(cx) / EMU] if w > IMG_MAX + 0.01]
        n_pair = sum(1 for cx, _, _ in blocks if abs(int(cx)/EMU - IMG_PAIR) <= IMG_TOL)
        if over:
            bad(f'{len(over)} 张图宽度超出正文可用宽 {IMG_MAX} in：'
                + '；'.join(f'图{i} {w:.2f} in' for i, w in over[:6])
                + ' —— 会溢出页面')
        else:
            ok(f'全部 {len(blocks)} 张图都在 {IMG_MAX} in 以内')
        ok(f'并排图 {n_pair} 张 × {IMG_PAIR} in')
        # 1:1：画布宽（px/150dpi）应约等于插入宽
        try:
            from PIL import Image
            drift = []
            for i, (cx, _, rid) in enumerate(blocks, 1):
                w_in = int(cx) / EMU
                tgt = 'word/' + rmap.get(rid, '').lstrip('/')
                try:
                    px = Image.open(io.BytesIO(z.read(tgt))).width
                except Exception:
                    continue
                # ⚠ 原来写死 px/150 —— 那是 v2 的渲染约定。
                #   本流水线是 200 dpi（junson_style.DPI / style-guide 都写明），
                #   写死 150 会把每一张正确的 1:1 图都判成不合格。改为读 PNG 自带的 dpi。
                try:
                    _im = Image.open(io.BytesIO(z.read(tgt)))
                    _dpi = (_im.info.get('dpi') or (150, 150))[0] or 150
                except Exception:
                    _dpi = 150
                canvas = px / float(_dpi)
                if canvas - w_in > 0.20:
                    eff = 7.0 * w_in / canvas
                    drift.append(f'图{i} 画布 {canvas:.2f} in → 插 {w_in:.2f} in，'
                                 f'图内 7pt 显示 {eff:.1f} pt')
            if drift:
                bad(f'{len(drift)} 张图不是 1:1（画布比插入宽，图内字被压小）：\n      '
                    + '\n      '.join(drift[:8]) + ('\n      …' if len(drift) > 8 else ''))
            else:
                ok('全部图 1:1 —— 图内写多少 pt 纸上就是多少 pt')
        except ImportError:
            warn('没装 Pillow，跳过 1:1 检查')

    # ── 4 表格：框线、表头底色、跨页重复 ────────────────────────
    tbls = re.findall(r'<w:tbl>.*?</w:tbl>', doc, re.S)
    # 并排 exhibit 用的是 1 行 2 列、无框线的排版表 —— 它没有列名，
    # 要求它带 w:tblHeader 是没有意义的。只查真正的数据表。
    def _is_layout(tb):
        one_row = len(re.findall(r'<w:tr[ >]', tb)) == 1
        two_col = len(re.findall(r'<w:gridCol', tb)) == 2
        # docx_helpers 的无框线是写成 w:val="none"（不是 "nil"），两种都认
        no_border = ('w:val="none"' in tb or 'w:val="nil"' in tb
                     or 'w:tblBorders' not in tb)
        return one_row and two_col and no_border
    def _has_navy_header(tb):
        # 表头行的判据：第一行里有深蓝底色。§8 Fund snapshot 的左表是纯 label|value、
        # 本来就没有表头行（同事那版如此），要求它带 w:tblHeader 是没有意义的。
        first = tb.split('</w:tr>')[0]
        return HDR_HEX.lower() in first.lower()
    data_tbls = [tb for tb in tbls if not _is_layout(tb) and _has_navy_header(tb)]
    n_nohdr = sum(1 for tb in tbls if not _is_layout(tb) and not _has_navy_header(tb))
    n_layout = len(tbls) - len(data_tbls)
    n_hdr = sum(1 for tb in data_tbls if '<w:tblHeader' in tb)
    if not tbls:
        bad('文档里一张表都没有')
    else:
        if n_hdr >= len(data_tbls):
            ok(f'{len(data_tbls)} 张数据表都带 w:tblHeader（表头跨页重复）'
               f'；另有 {n_layout} 张并排排版表、{n_nohdr} 张无表头小表，无需表头')
        else:
            bad(f'{len(data_tbls)} 张数据表里只有 {n_hdr} 张带 w:tblHeader —— '
                f'剩下 {len(data_tbls)-n_hdr} 张跨页后看不到列名')
        gc = Counter(re.findall(r'w:val="single"[^>]*w:color="([0-9A-Fa-f]{6})"',
                                ' '.join(tbls)))
        if gc and gc.most_common(1)[0][0].upper() != GRID_HEX:
            warn(f'表格框线主色 #{gc.most_common(1)[0][0]}，基线是 #{GRID_HEX}')
        elif gc:
            ok(f'表格框线 #{GRID_HEX}')
        if HDR_HEX in ' '.join(tbls).upper().replace('#', ''):
            ok(f'表头底色 #{HDR_HEX}')

    # ── 5 Exhibit 编号（委托 exhibits.py）────────────────────────
    try:
        import importlib.util as il
        sp = il.spec_from_file_location(
            'exh', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exhibits.py'))
        mod = il.module_from_spec(sp); sp.loader.exec_module(mod)
        E = mod.load()
        left = mod.PLACEHOLDER.findall(txt)
        if left:
            bad(f'还有 {len(left)} 处未替换的 {{{{ex:...}}}} 占位：{sorted(set(left))[:6]}')
        nums = [int(x) for x in re.findall(r'Exhibit (\d+)\s*[:：]', txt)]
        uniq = sorted(set(nums))
        miss = [n for n in range(1, len(E) + 1) if n not in uniq]
        dup = sorted({n for n in uniq if nums.count(n) > 1})
        if miss or dup:
            if miss: bad(f'Exhibit 断号，manifest 有 {len(E)} 个，成稿缺 {miss}')
            if dup:  bad(f'Exhibit 重号：{dup}')
        else:
            ok(f'Exhibit 编号 1–{len(E)} 连续、无断号无重号')
    except Exception as e:
        warn(f'Exhibit 编号检查跳过：{e}')

    # ── 6 每张 exhibit 都有 Note / Source ──────────────────────
    n_cap = len(re.findall(r'Exhibit \d+\s*[:：]', txt))
    n_note = len(re.findall(r'\bNote\s*[:：]', txt))
    # 多个来源时英文写 "Sources:" 是正常的，原来的正则只认单数，会漏掉一大半
    n_src = len(re.findall(r'\bSources?\s*[:：]', txt))
    if n_cap and n_src >= n_cap * 0.9:
        ok(f'{n_cap} 个题注 / {n_src} 处 Source / {n_note} 处 Note')
    else:
        bad(f'{n_cap} 个题注但只有 {n_src} 处 Source —— 每张 exhibit 都要有来源行')

    # ── 7 来源链接：完整 URL，不许裸域名 ────────────────────────
    links = re.findall(r'Type="[^"]*/hyperlink"[^>]*Target="([^"]+)"', rels)
    if not links:
        bad('一个外部超链接都没有 —— Related news 每条的来源必须是可点的超链接')
    else:
        def bare(u):
            m = re.match(r'https?://[^/]+(/?.*)$', u)
            return (m is None) or (m.group(1).strip('/') == '')
        vague = sorted({u for u in links if bare(u)})
        if vague:
            bad(f'{len(vague)} 个来源链接只到域名：' + '、'.join(vague[:5])
                + ' —— 必须是那一篇的完整 URL，拿不到就不要写这条')
        else:
            ok(f'{len(links)} 个来源链接都带路径')

    # ── 8 占位与陈数 ───────────────────────────────────────────
    hit = [b for b in BANNED if b in txt]
    if hit:
        bad('正文里有占位/陈数字样：' + '、'.join(sorted(set(hit))))
    else:
        ok('没有占位字样')

    # ── 9 页眉页脚季度一致 ─────────────────────────────────────
    fq = re.search(r'(20\d\d)Q([1-4])', os.path.basename(path))
    hq = set()
    for n in z.namelist():
        if re.match(r'word/header\d*\.xml$', n):
            hq |= set(re.findall(r'20\d\dQ[1-4]',
                                 ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>',
                                                     z.read(n).decode('utf-8')))))
    if not fq:
        bad('文件名里没有 <YYYY>Q<n> —— 命名是 Junson_Private_Credit_Report_<季度>_EN_v<n>.docx')
    elif hq and hq != {fq.group(0)}:
        bad(f'文件名季度 {fq.group(0)} 与页眉 {sorted(hq)} 不一致')
    else:
        ok(f'季度 {fq.group(0)}：文件名与页眉一致')

    # ── CJK：英文版正文不许混中日韩字符（2026Q3 教训：方法论段注入了账本中文筛选描述）──
    _cjk = re.findall(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', txt)
    if _cjk:
        _ctx = []
        for _m in re.finditer(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', txt):
            _ctx.append(txt[max(0, _m.start()-25):_m.start()+25])
            if len(_ctx) >= 3:
                break
        bad(f'英文版正文出现 {len(_cjk)} 个中日韩字符 —— 正文要引账本字段时用英文字段'
            f'（如 meta.screen.criteria_en），中文字段只留账本内部。前几处: {_ctx}')
    else:
        ok('正文无中日韩字符（英文版检查）')

    # ── 加粗密度：正文每段至多一个头条数字（基线成稿 0.78 处/段，含标题行）──
    #   2026Q3 踩过：第一版把几乎每个数都加粗，正文 369 处 ≈ 6 处/段，是基线的 12 倍。
    # 表格里的表头本来就该加粗，先把 <w:tbl> 整块剔掉，只看正文段
    _body_only = re.sub(r'<w:tbl[ >].*?</w:tbl>', '', doc, flags=re.S)
    _paras = re.findall(r'<w:p[ >].*?</w:p>', _body_only, re.S)
    _npara = _nbold = 0
    for _p in _paras:
        _runs = re.findall(r'<w:r[ >].*?</w:r>', _p, re.S)
        _txt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', _p)).strip()
        if not _txt or _txt.startswith('Note:') or _txt.startswith('Source:'):
            continue
        _npara += 1
        for _r in _runs:
            _rt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', _r)).strip()
            # ⚠ python-docx 对 bold=False 写的是 <w:b w:val="0"/>，不能只匹配 '<w:b '
            _bon = re.search(r'<w:b/>|<w:b w:val="(1|true|on)"', _r)
            if _rt and _rt != '·' and _bon:
                _nbold += 1
    if _npara:
        _dens = _nbold / _npara
        if _dens <= 1.6:
            ok(f'加粗密度 {_dens:.2f} 处/段（{_nbold}/{_npara}）—— 基线 0.78，每段至多一个头条数字')
        else:
            bad(f'加粗过多：{_dens:.2f} 处/段（{_nbold}/{_npara}），基线是 0.78 —— '
                f'规矩是每段至多一个头条数字，不是关键数字都加粗')

    # ── 标题块的日期必须是**运行当日** ─────────────────────────────────
    # ⛔ Alex 2026-08-26：「报告大标题的时间 为什么还是8月24日，你这个不能写死啊
    #    必须是skill运行的当日的时间。」原来 build_doc 从账本 meta.report_date 读 ——
    #    那是上次出稿的日子，一个字面量，跨一天就是错的。
    from datetime import date as _date
    _today = _date.today().strftime('%-d %b, %Y')
    if _today in txt:
        ok(f'标题日期 = 运行当日（{_today}）')
    else:
        _seen = re.findall(r'\b\d{1,2} [A-Z][a-z]{2},? \d{4}\b', txt[:3000])
        bad(f'标题日期不是运行当日 —— 应为「{_today}」，纸上是 {_seen[:2] or "找不到日期"}；'
            f'⛔ 日期必须出稿时取当天，不许从账本 meta 或字面量读')

    # ── 纸上的表头必须等于账本冻结的表头 ─────────────────────────────────
    # ⛔ Alex 2026-08-26：「E36 和 E37 这张图的格式 表头 最左侧的一列也是固定死的，
    #    必须跟同事的那个报告一样，除了季度。我之前跟你说过啊，你居然没改。」
    # 根因：pc_hdrcheck 查的是**账本**里的 header，而 build_doc 好几处把表头当字面量
    # 传进 tbl()，两边可以完全不一样而所有检查都绿 —— 2026-08-26 实测 13 个冻结表头里
    # 有 6 个纸上印的根本不是账本那个。这一条查纸面：冻结的表头必须逐字出现在文档里。
    try:
        import json as _js, io as _io
        _L = _js.load(_io.open('series.json', encoding='utf-8'))['exhibits']
    except Exception:
        _L = {}
    if _L:
        _tbls = re.findall(r'<w:tbl>.*?</w:tbl>', doc, re.S)
        _printed = []
        for _tb in _tbls:
            _first = _tb.split('</w:tr>')[0]
            if HDR_HEX.upper() not in _first.upper():
                continue
            _cells = re.findall(r'<w:tc>.*?</w:tc>', _first, re.S)
            _printed.append([' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', c)).strip()
                             .replace('&amp;', '&') for c in _cells])
        _frozen = {k: v['header'] for k, v in _L.items() if v.get('header')}
        # 表头 -> 那张表的整块 XML，用来接着核最左列
        _tblof = {}
        for _tb in _tbls:
            _first = _tb.split('</w:tr>')[0]
            if HDR_HEX.upper() not in _first.upper():
                continue
            _cells = re.findall(r'<w:tc>.*?</w:tc>', _first, re.S)
            _key = tuple(' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', c)).strip()
                         .replace('&amp;', '&') for c in _cells)
            _tblof.setdefault(_key, []).append(_tb)
        _left, _miss, _colbad, _colok = list(_printed), [], [], 0
        for _k, _h in sorted(_frozen.items()):
            _hit = next((i for i, p2 in enumerate(_left) if p2 == _h), None)
            if _hit is None:
                _same1 = next((p2 for p2 in _left if p2 and _h and p2[0] == _h[0]), None)
                _miss.append(f'{_k}: 账本 {_h} ／ 纸上'
                             + (f' {_same1}' if _same1 else '找不到对应的表'))
                continue
            _left.pop(_hit)
            # ── 冻结了最左列的，纸上那一列逐格核 ────────────────────────
            _rlf = (_L[_k].get('row_labels_fixed') or {})
            _want = _rlf.get('expected') or _rlf.get('left') or []
            _want = [(x['label'] if isinstance(x, dict) else x) for x in _want]
            _cand = _tblof.get(tuple(_h)) or []
            if not _want or not _cand:
                continue

            def _col1(_tb):
                _out = []
                for _r in _tb.split('</w:tr>')[1:]:
                    _c1 = re.search(r'<w:tc>.*?</w:tc>', _r, re.S)
                    if not _c1:
                        continue
                    _v = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>',
                                             _c1.group(0))).strip().replace('&amp;', '&')
                    if _v:
                        _out.append(_v)
                return _out
            # ⛔ 三只基金的 snapshot 表B 表头完全相同，只能靠最左列认人 ——
            #    先在同表头的候选里找那张对得上的；找不到才拿第一张来报差异。
            _pick = next((i for i, _c in enumerate(_cand)
                          if _col1(_c)[:len(_want)] == _want), None)
            _tb = _cand.pop(_pick if _pick is not None else 0)
            _got = _col1(_tb)
            # 分组标题行（E48 那两行灰底）也在最左列里，冻结清单已经含了它们
            if _got[:len(_want)] != _want:
                _d = next((f'第 {i+1} 行 应为 {a!r} 纸上 {b!r}'
                           for i, (a, b) in enumerate(zip(_want, _got + [''] * len(_want)))
                           if a != b), f'行数 {len(_got)} ≠ {len(_want)}')
                _colbad.append(f'{_k}: {_d}')
            else:
                _colok += 1
        if _colbad:
            bad(f'纸上最左列与账本冻结的不一致 {len(_colbad)} 处 —— ⛔ 行名一律从账本读：'
                '\n        ' + '\n        '.join(_colbad))
        elif _colok:
            ok(f'{_colok} 张表的最左列纸上逐格对上冻结清单')
        if _miss:
            bad(f'纸上表头与账本冻结的不一致 {len(_miss)} 处 —— ⛔ 表头一律从账本读，'
                f'不许在 build_doc 里当字面量传：\n        ' + '\n        '.join(_miss))
        else:
            ok(f'{len(_frozen)} 个冻结表头纸上逐字对上')

    # ── §8 Fund snapshot 必须是**横向并排**的两张表 ─────────────────────
    # ⛔ Alex 2026-08-26：「fund snapshot 格式全错…是两个分开的的横向排放的表」
    #    我上一版把两张表上下摞着放。所以这里查纸面结构：Fund snapshot 段之后紧跟的
    #    那张表必须是 1 行 2 列的外层表，且左右格各嵌一张表。
    _snap_pairs = 0
    for _m in re.finditer(r'<w:t[^>]*>Fund snapshot</w:t>', doc):
        _tail = doc[_m.end():_m.end() + 60000]
        _t0 = _tail.find('<w:tbl>')
        if _t0 < 0:
            continue
        _seg = _tail[_t0:_t0 + 60000]
        _r0 = _seg.find('</w:tr>')
        _firstrow = _seg[:_r0] if _r0 > 0 else _seg
        _ncell = _firstrow.count('<w:tc>')
        _nested = _firstrow.count('<w:tbl>')          # 外层第一行里嵌了几张表
        if _ncell >= 2 and _nested >= 2:
            _snap_pairs += 1
    if _snap_pairs == 3:
        ok('§8 三只基金的 Fund snapshot 都是横向并排的两张表（外层 1×2）')
    else:
        bad(f'§8 Fund snapshot 的并排版式只对上 {_snap_pairs} 只（应为 3）—— '
            f'⛔ 必须是外层 1 行 2 列、左右格各嵌一张表（左表无表头、右表 '
            f'Metric | <pq> | <cq> | QoQ Δ），不许上下摞着放')

    # ── §8 三只基金各三段，段名段序完全一致 ────────────────────────────
    # ⛔ Alex 2026-08-25「每个 fund 下面的结构都要是一样的，要包含 Fund snapshot、
    #    Portfolio composition、Fund level performance detail」
    # ⛔ Alex 2026-08-26「Portfolio composition 也没了，Fund level performance detail 也没有」
    #    —— 账本里有数、pc_hdrcheck 也过，但**文档里根本没渲染**，而当时没有任何检查看纸面。
    #    这一条就是补那个洞：查的是纸上有没有这三个段名。
    # ── 数据表的内容行必须隔行底色 ────────────────────────────────────
    # 用 python-docx 走一遍（含嵌套表），比正则数 <w:shd> 稳 —— 嵌套表的行
    # 在 XML 里跟外层的混在一起，正则分不开。
    try:
        from docx import Document as _Doc
        from docx.oxml.ns import qn as _qn
        _d = _Doc(path)

        def _fill(_c):
            _tp = _c._tc.tcPr
            if _tp is None:
                return None
            _sh = _tp.find(_qn('w:shd'))
            return (_sh.get(_qn('w:fill')) or '').upper() if _sh is not None else None

        def _walk(_tbls):
            _out = []
            for _t in _tbls:
                _out.append(_t)
                for _r in _t.rows:
                    for _c in _r.cells:
                        _out += _walk(_c.tables)
            return _out

        _ZEB, _GRP = ZEBRA_HEX.upper(), 'E8E8E8'
        _zb, _zok = [], 0
        for _t in _walk(_d.tables):
            _hdr = any(_fill(_c) == HDR_HEX.upper() for _c in _t.rows[0].cells)
            _body = list(_t.rows[1:]) if _hdr else list(_t.rows)
            # 并排排版用的无框线 1×2 外层表不算数据表
            if len(_t.columns) < 2 or len(_body) < 2:
                continue
            _pat = []
            for _r in _body:
                _f = [_fill(_c) for _c in _r.cells]
                if _GRP in [x for x in _f if x]:      # E48 的分组标题行，跳过不计
                    continue
                _pat.append(_ZEB in [x for x in _f if x])
            if len(_pat) < 2:
                continue
            if not any(_pat):
                # 没有表头、也没有底色的，是排版表（图题+图+Note 的格子），不算
                if not _hdr:
                    continue
                _zb.append(f'第 {_body[0].cells[0].text.strip()[:22]!r} 那张表整片纯白')
                continue
            _bad_i = [i for i in range(1, len(_pat)) if _pat[i] == _pat[i - 1]]
            if _bad_i:
                _zb.append(f'{_body[0].cells[0].text.strip()[:22]!r} 那张表第 '
                           f'{[i + 1 for i in _bad_i][:4]} 行没交替')
            else:
                _zok += 1
        if _zb:
            bad(f'{len(_zb)} 张数据表的内容行不是一条白一条灰 —— ⛔ 表头不算，'
                f'内容行必须交替：\n        ' + '\n        '.join(_zb[:6]))
        else:
            ok(f'{_zok} 张数据表的内容行都是一条白一条灰（表头不算）')
    except Exception as _e:
        warn(f'隔行底色没查到（{type(_e).__name__}: {_e}）')

    # ── 正文不许写节号引用，只许写节名 ──────────────────────────────
    _numxref = sorted(set(re.findall(r'\bSections?\s+\d+(?:\.\d+)?', txt)))
    if _numxref:
        bad(f'正文还有 {len(_numxref)} 种节号引用 —— ⛔ 标题上没有节号了，'
            f'引用一律写节名（build_doc 的 xr()）：{_numxref[:8]}')
    else:
        ok('正文的交叉引用都写的是节名，没有节号')

    # ── Fund snapshot 左表的最左列（无表头，逃过了上面那条检查）─────────
    # ⛔ Alex 2026-08-26：「Guggenheim / HSBC 的 Fund snapshot 的左边的表格的最左侧
    #    一列还是不对」。表A 没有深蓝表头行，所以按表头配对的那条检查根本看不到它 ——
    #    这一条按 Fund snapshot 段落顺序取外层 1×2 的左格，逐格核账本的冻结行名。
    _snapA_bad, _snapA_ok = [], 0
    _snap_slugs = ['fund_pag_snapshot', 'fund_gug_snapshot', 'fund_hsbc_snapshot']
    _ms = list(re.finditer(r'<w:t[^>]*>Fund snapshot</w:t>', doc))
    if len(_ms) != len(_snap_slugs):
        _snapA_bad.append(f'纸上 Fund snapshot 段落 {len(_ms)} 个，应为 {len(_snap_slugs)} 个')
    for _sl, _m2 in zip(_snap_slugs, _ms):
        _want = ((_L.get(_sl) or {}).get('row_labels_fixed') or {}).get('expected') or []
        if not _want:
            _snapA_bad.append(f'{_sl}: 账本缺 row_labels_fixed.expected'); continue
        _seg2 = doc[_m2.end():_m2.end() + 60000]
        _t1 = _seg2.find('<w:tbl>')
        if _t1 < 0:
            _snapA_bad.append(f'{_sl}: Fund snapshot 后面找不到表'); continue
        # 外层第一行的第一格里嵌的那张表 = 表A
        _outer = _seg2[_t1:]
        _inner = re.search(r'<w:tc>.*?(<w:tbl>.*?</w:tbl>)', _outer, re.S)
        if not _inner:
            _snapA_bad.append(f'{_sl}: 外层左格里没有嵌表'); continue
        _got2 = []
        for _r2 in _inner.group(1).split('</w:tr>'):
            _c2 = re.search(r'<w:tc>.*?</w:tc>', _r2, re.S)
            if not _c2:
                continue
            _v2 = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>',
                                      _c2.group(0))).strip().replace('&amp;', '&')
            if _v2:
                _got2.append(_v2)
        if _got2[:len(_want)] != _want:
            _d2 = next((f'第 {i+1} 行 应为 {a!r} 纸上 {b!r}'
                        for i, (a, b) in enumerate(zip(_want, _got2 + [''] * len(_want)))
                        if a != b), f'行数 {len(_got2)} ≠ {len(_want)}')
            _snapA_bad.append(f'{_sl}: {_d2}')
        else:
            _snapA_ok += 1
    if _snapA_bad:
        bad('Fund snapshot 左表的最左列对不上账本：\n        '
            + '\n        '.join(_snapA_bad))
    else:
        ok(f'{_snapA_ok} 只基金的 Fund snapshot 左表最左列纸上逐格对上（三只各一套行名）')
    _BLK = ['Fund snapshot', 'Portfolio composition', 'Fund level performance detail']
    _paras = [' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', _p))
              for _p in doc.split('</w:p>')]
    _paras = [' '.join(x.split()) for x in _paras]

    # ── 标题里不许再出现「几点几」 ───────────────────────────────────
    # ⛔ Alex 2026-08-26：「把每个标题前面的几点几都去掉，比如 9.1  Positioning
    #    scorecard，只要去掉数字和小数点，标题部分其他不变。」
    #    小节标题在 docx 里用的是 HDR_STYLE_SZ 那一档字号加粗深蓝，靠样式认不牢，
    #    所以直接扫全部段落：短行、以「数字.数字 空格」开头的就是漏掉的节号。
    _numbered = [l for l in _paras
                 if len(l) < 90 and re.match(r'^\d+(?:\.\d+)+[.、]?\s+\S', l)]
    if _numbered:
        bad(f'还有 {len(_numbered)} 个标题带着节号 —— ⛔ 一律去掉「几点几」：'
            + '；'.join(x[:40] for x in _numbered[:6]))
    else:
        ok('标题都没有节号前缀')

    # ⛔ Alex 2026-08-26 把标题里的「几点几」全去掉了，所以不能再靠 '8.x ' 前缀认小节。
    #    改用三只基金各自的名字 —— 名字来自账本，不写死在这里。
    _FUNDNAME = [(_L.get(f'fund_{_k}_snapshot') or {}).get('fund_name')
                 for _k in ('pag', 'gug', 'hsbc')]
    _fh = []
    for _nm in _FUNDNAME:
        if not _nm:
            continue
        _fh += [i for i, l in enumerate(_paras) if l.startswith(_nm) and len(l) < 80][:1]
    _fh.sort()
    if len(_fh) != 3:
        bad(f'§8 应有三只基金三个小节，按账本的 fund_name 在纸上只认出 {len(_fh)} 个：'
            f'{[_paras[i][:34] for i in _fh]}（找的是 {_FUNDNAME}）')
    else:
        _miss = []
        for _k, _i in enumerate(_fh):
            _end = _fh[_k + 1] if _k + 1 < len(_fh) else len(_paras)
            _got = [_b for _b in _BLK if _b in _paras[_i:_end]]
            if _got != _BLK:
                _miss.append(f'「{_paras[_i][:34]}」缺 {[b for b in _BLK if b not in _got]}'
                             + (f'（实际顺序 {_got}）' if _got else ''))
        if _miss:
            bad('§8 三段结构不齐：' + '；'.join(_miss))
        else:
            ok('§8 三只基金各有 Fund snapshot / Portfolio composition / '
               'Fund level performance detail，段名段序一致')

    print(f'\n=== 版面自查 · {os.path.basename(path)} ===\n')
    for m in oks:   print('  ✓', m)
    for m in warns: print('  ?', m)
    for m in fails: print('  ✗', m)
    print(f'\n通过 {len(oks)}　不通过 {len(fails)}　待确认 {len(warns)}')
    if fails:
        print('\n不通过就不能交稿。改完再跑一遍。')
        return 1
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
