#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exhibit 编号的唯一来源 —— 从 manifest 推，正文永不写死数字。

用法（出稿脚本里）：
    import exhibits
    EX = exhibits.load()                  # slug -> {n, caption, layout, section}
    EX.n('mkt_aum_by_channel')            # -> 1
    EX.caption('mkt_aum_by_channel')      # -> 'Exhibit 1: Private debt AUM ...'
    exhibits.resolve('见 {{ex:cf_fitch_ttm_default}}')   # -> '见 Exhibit 17'

命令行：
    python3 exhibits.py                   # 打印全表
    python3 exhibits.py --check REPORT.docx   # 查成稿里编号连续、无断号、无重号、无残留占位

为什么这么做：58 个编号手工维护，增删一张图后面全要重排，第二季必错。
正文里一律写 {{ex:slug}}，编号在最后一步统一替换。
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "exhibit_manifest.json")
PLACEHOLDER = re.compile(r'\{\{ex:([a-z0-9_]+)\}\}')


class Exhibits:
    def __init__(self, entries):
        self._by_slug = {}
        self._order = []
        self.skipped = set()
        n = 0
        for e in entries:
            if e.get('skip'):
                # 本季不出的图不占号：可选图，以及缺源文件而整块删掉的图（账本 meta.skipped）
                self.skipped.add(e['slug'])
                continue
            n += 1
            rec = dict(e); rec['n'] = n
            self._by_slug[e['slug']] = rec
            self._order.append(rec)
        # 并排的两张删了一张：剩下那张改为单独一行，不留半边空位
        for i, rec in enumerate(self._order):
            nxt = self._order[i + 1] if i + 1 < len(self._order) else None
            prv = self._order[i - 1] if i > 0 else None
            if rec.get('layout') == 'pairL' and not (nxt and nxt.get('layout') == 'pairR'):
                rec['layout'] = 'solo'
            elif rec.get('layout') == 'pairR' and not (prv and prv.get('layout') == 'pairL'):
                rec['layout'] = 'solo'

    def __len__(self):
        return len(self._order)

    def __iter__(self):
        return iter(self._order)

    def n(self, slug):
        if slug not in self._by_slug:
            raise KeyError(f'manifest 里没有这个 slug: {slug}')
        return self._by_slug[slug]['n']

    def caption(self, slug, **fmt):
        r = self._by_slug[slug]
        cap = r['caption']
        if fmt:
            try:
                cap = cap.format(**fmt)
            except KeyError as ex:
                raise KeyError(f'{slug} 的题注缺占位值 {ex}') from None
        # 以前只在「传了 fmt 但缺键」时报错；一个 fmt 都没传的调用直接跳过格式化，
        # 于是 {cq}/{tot} 这种原样印进了成稿。凡是留下花括号就一律拦住。
        left = re.findall(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', cap)
        if left:
            raise KeyError(
                f'{slug} 的题注还剩占位 {left} 没填 —— caption() 调用时没传这些值。'
                f'\n  题注原文：{r["caption"]}'
                f'\n  动态题注必须逐个把值从账本读出来传进来，不许让花括号印到纸上。')
        return f"Exhibit {r['n']}: {cap}"

    def rec(self, slug):
        return self._by_slug[slug]

    def pairs(self):
        """返回 [(左 slug, 右 slug), ...] —— 并排组，给 exhibit_pair() 用。"""
        out, i = [], 0
        o = self._order
        while i < len(o):
            if o[i]['layout'] == 'pairL':
                if i + 1 >= len(o) or o[i + 1]['layout'] != 'pairR':
                    raise ValueError(f"{o[i]['slug']} 标了 pairL 但下一个不是 pairR —— manifest 顺序错了")
                out.append((o[i]['slug'], o[i + 1]['slug'])); i += 2
            else:
                i += 1
        return out


def skipped_slugs(ledger=None):
    """本季因缺源文件而删掉的 exhibit：账本 meta.skipped 里 rq 等于本季的那些条目
    （[{"slug", "missing", "rq"}]）。删掉的图不占编号，所有脚本经 load() 自动跳过它们。"""
    path = ledger or os.environ.get('PC_LEDGER', 'series.json')
    if not os.path.exists(path):
        return ()
    meta = json.load(io.open(path, encoding='utf-8')).get('meta', {})
    rq = meta.get('rq')
    return tuple(s['slug'] for s in meta.get('skipped', []) if isinstance(s, dict) and s.get('rq') == rq and s.get('slug'))


def load(skip_slugs=None):
    if skip_slugs is None:
        skip_slugs = skipped_slugs()
    m = json.load(io.open(MANIFEST, encoding='utf-8'))
    ents = [dict(e, skip=(e['slug'] in skip_slugs)) for e in m['exhibits']]
    return Exhibits(ents)


def resolve(text, ex=None):
    """把正文里的 {{ex:slug}} 换成 'Exhibit N'。未知 slug 直接报错，不静默留占位。"""
    ex = ex or load()
    unknown = []

    def sub(mo):
        sl = mo.group(1)
        try:
            return f'Exhibit {ex.n(sl)}'
        except KeyError:
            unknown.append(sl); return mo.group(0)
    out = PLACEHOLDER.sub(sub, text)
    if unknown:
        raise KeyError(f'正文引用了 manifest 里没有的 slug: {sorted(set(unknown))}')
    return out


# ── 成稿检查 ──────────────────────────────────────────────────────────
def check_docx(path):
    import zipfile
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    txt = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', doc))
    ex = load()
    fails = []

    left = PLACEHOLDER.findall(txt)
    if left:
        fails.append(f'成稿里还有 {len(left)} 处未替换的 {{{{ex:...}}}} 占位：{sorted(set(left))[:6]}')

    # 另一类占位：动态题注的 {cq} / {tot} 这种 str.format 字段。
    # 2026Q3 踩过：5 个动态题注因为 caption() 没收到值，花括号原样印进了成稿，
    # 而这里只查 {{ex:...}}，硬查也查不出来 —— 所以两类都要查。
    braces = sorted(set(re.findall(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', txt)))
    if braces:
        fails.append(f'成稿里还有 {len(braces)} 种未填的题注占位 {braces} '
                     '—— 动态题注的值没传进 caption()；应当从账本的 caption_rendered 取')

    nums = sorted(set(int(x) for x in re.findall(r'Exhibit (\d+)\s*[:：]', txt)))
    if not nums:
        fails.append('成稿里一个 "Exhibit N:" 题注都没有')
    else:
        want = list(range(1, len(ex) + 1))
        missing = [n for n in want if n not in nums]
        extra = [n for n in nums if n > len(ex)]
        if missing:
            fails.append(f'题注断号：manifest 有 {len(ex)} 个 exhibit，成稿缺 {missing}')
        if extra:
            fails.append(f'题注超出 manifest 范围：{extra}')
        # 重号
        allnums = [int(x) for x in re.findall(r'Exhibit (\d+)\s*[:：]', txt)]
        dup = sorted({n for n in allnums if allnums.count(n) > 1})
        if dup:
            fails.append(f'题注重号：{dup}')

    print(f'\n=== Exhibit 编号自查 · {os.path.basename(path)} ===\n')
    print(f'  manifest 定义 {len(ex)} 个；成稿题注 {len(nums)} 个')
    if fails:
        for f in fails:
            print('  ✗', f)
        print('\n不通过。编号只能由 exhibits.py 生成，不要手写。')
        return 1
    print('  ✓ 编号 1–%d 连续、无断号、无重号、无残留占位' % len(ex))
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--check':
        sys.exit(check_docx(sys.argv[2]))
    ex = load()
    print(f'{len(ex)} 个 exhibit：\n')
    cur = None
    for r in ex:
        if r['section'] != cur:
            cur = r['section']; print(f'  ── §{cur}')
        tag = {'pairL': '┌ 并排', 'pairR': '└ 并排', 'table': '  表  ', 'solo': '  单图'}[r['layout']]
        print(f'  {r["n"]:>2} {tag}  {r["slug"]:<28} {r["caption"][:56]}')
    print(f'\n并排组 {len(ex.pairs())} 对')
