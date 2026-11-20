#!/usr/bin/env python3
"""阶段一的签收闸门。阶段二没有它就不许启动。

  python3 approve.py --sign     阶段一跑完、用户校对通过后落签收
  python3 approve.py --check    阶段二启动前校验（exit 0 通过 / 1 拒绝）
  python3 approve.py --diff     校验失败时用：逐字段说清账本改了什么，
                                并区分「会画到图上」与「只是文字/派生字段」

签收文件记 CQ、每张图的 sha256、series.json 的 sha256。
只要有任何一张图被重出、或账本被改过，校验就失败 —— 必须重新校对再签。
这样跨会话也成立：阶段二可以是全新一次会话。
"""
import hashlib, io, json, os, sys, glob

CHARTS = 'charts'      # 图落在 charts/，out/ 放核对清单与打包
OUT = 'out'
SER = 'series.json'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def cq():
    """签收标签用报告季 rq。

    早前这里读的是 meta['cq']，但账本改版后季度字段是 meta['rq']（报告季，即撰写季），
    各层的数据基准日分别放在 meta['as_of'].{market,fund,competitor} 里。
    保留对老字段的回退，免得旧账本签不动。
    """
    m = json.load(open(SER, encoding='utf-8'))['meta']
    q = m.get('rq') or m.get('cq')
    if not q:
        raise SystemExit('series.json 的 meta 里既没有 rq 也没有 cq —— 无法确定季度，拒绝签收')
    return q


def tag(c):
    return c.replace("'", '').replace(' ', '')


def path_for(c):
    n = f'APPROVED_{tag(c)}.json'
    # 兼容两种落点：早期签在 out/，现在签在工作目录
    return n if os.path.exists(n) else (os.path.join(OUT, n) if os.path.exists(os.path.join(OUT, n)) else n)


def ledger_copy_for(c):
    """签收时把账本原样存一份 —— 否则事后只知道「变了」，不知道「变了什么」。"""
    return os.path.join(OUT, f'APPROVED_{tag(c)}_series.json')


def manifest():
    """图在 charts/ 里（早前这里扫的是 out/，扫不到东西，签收永远失败）。"""
    files = sorted(glob.glob(os.path.join(CHARTS, '*.png')))
    return {os.path.basename(p): sha(p) for p in files}


def sign():
    c = cq()
    m = manifest()
    if not m:
        sys.exit(f'{CHARTS}/ 里没有 PNG，阶段一还没跑完')
    rec = {'rq': c, 'cq': c, 'series_sha256': sha(SER), 'files': m, 'count': len(m)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(path_for(c), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 连账本一起归档：以后 --check 失败时能直接说清改了哪个字段，
    # 而不是只丢一句「被改过」让人回去猜。
    lc = ledger_copy_for(c)
    io.open(lc, 'w', encoding='utf-8').write(io.open(SER, encoding='utf-8').read())
    print(f'[signed] {path_for(c)}  CQ={c}  {len(m)} 张图')
    print(f'[archived] {lc}  ← 签收时的账本原样,给 --diff 用')
    print('阶段二现在可以启动（可以是新会话）。')


def check():
    c = cq()
    p = path_for(c)
    if not os.path.exists(p):
        n = len(manifest())
        sys.exit(f'✗ 拒绝启动阶段二：没有 {p}。\n'
                 f'  阶段一必须先跑完、把这 {n} 张图和核对清单交给用户逐项校对、'
                 f'用户确认后才能 approve.py --sign。\n'
                 f'  不许跳过这一步用默认值往下走 —— 定时任务场景下也必须停在这里。')
    rec = json.load(open(p, encoding='utf-8'))
    bad = []
    if (rec.get('rq') or rec.get('cq')) != c:
        bad.append(f'签收的季度是 {rec.get("rq") or rec.get("cq")}，账本现在是 {c}')
    if rec.get('series_sha256') != sha(SER):
        bad.append('series.json 在签收之后被改过 —— 数据变了，图和签收都作废')
    now = manifest()
    for fn, h in rec.get('files', {}).items():
        if fn not in now:
            bad.append(f'签收时有 {fn}，现在不见了')
        elif now[fn] != h:
            bad.append(f'{fn} 在签收之后被重出过')
    for fn in now:
        if fn not in rec.get('files', {}):
            bad.append(f'{fn} 是签收之后新增的，没被校对过')
    if bad:
        sys.exit('✗ 签收失效，阶段二拒绝启动：\n  - ' + '\n  - '.join(bad)
                 + '\n  先跑 approve.py --diff 看清到底改了哪个字段 ——'
                   '会画到图上的字段动了就必须重出图、重交清单;'
                   '只是文字或派生字段动了,图不用重出,但仍要用户看过再 --sign。')
    print(f'✓ 签收有效：CQ={c}，{rec["count"]} 张图，账本未变。阶段二可以开始。')


PLOTTED = ('periods', 'labels', 'stacks', 'lines', 'rhs_line', 'bars', 'groups',
           'shares', 'rows', 'points', 'bands', 'vals', 'values', 'history',
           'median', 'p25', 'p75', 'iqr', 'ylim', 'yticks')


def _flat(o, p=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _flat(v, p + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _flat(v, p + (f'[{i}]',))
    else:
        yield '/'.join(p), o


def diff():
    """讲清账本自签收以来改了什么,并分成两类：
       · 会画到图上的字段  —— 图必须重出、清单必须重交、必须重签
       · 只是文字/派生字段 —— 图没动,重签是补记录,不是重做"""
    c = cq()
    lc = ledger_copy_for(c)
    if not os.path.exists(lc):
        sys.exit(f'✗ 没有 {lc} —— 这次签收是在归档功能加进来之前落的,'
                 '无法给出字段级差异。\n'
                 '  能给的旁证是：把 charts/ 备份后按当前账本重出一遍,'
                 '逐张比像素;全都一致就说明图上的数一个都没动。')
    a = dict(_flat(json.load(io.open(lc, encoding='utf-8'))))
    b = dict(_flat(json.load(io.open(SER, encoding='utf-8'))))
    added = [k for k in b if k not in a]
    removed = [k for k in a if k not in b]
    changed = [k for k in a if k in b and a[k] != b[k]]

    def is_plotted(k):
        # series_bank 是「找定了先存着」的序列，当季没有任何出图脚本读它 ——
        # 动它不会改变任何一张 PNG，所以不算 h，否则每存一条 46 期的序列就把签收作废一次。
        if k.split('/')[0] == 'series_bank':
            return False
        return any(seg in PLOTTED for seg in k.split('/'))

    def exhibit_of(k):
        parts = k.split('/')
        if parts[0] == 'series_bank':
            return f'(bank) {parts[1]}' if len(parts) > 1 else '(bank)'
        return parts[1] if len(parts) > 1 and parts[0] == 'exhibits' else '(meta)'

    # 先按 exhibit 汇总 —— 几百行字段级 diff 没人看得完，要签的是「哪几张图动了」
    roll = {}
    for tag, keys in (('新增', added), ('删除', removed), ('改动', changed)):
        for k in keys:
            e = roll.setdefault(exhibit_of(k), {'新增': [0, 0], '删除': [0, 0], '改动': [0, 0]})
            e[tag][0 if is_plotted(k) else 1] += 1
    print('\n═══ 按 exhibit 汇总（h = 会画到图上 / t = 只是文字或派生字段）═══\n')
    print('%-32s %-14s %-14s %-14s' % ('exhibit', '新增 h/t', '删除 h/t', '改动 h/t'))
    hot_ex = []
    for name in sorted(roll, key=lambda n: -sum(v[0] for v in roll[n].values())):
        r = roll[name]
        if sum(r[t][0] for t in r):
            hot_ex.append(name)
        print('%-32s %-14s %-14s %-14s' % (
            name,
            '%d/%d' % tuple(r['新增']), '%d/%d' % tuple(r['删除']), '%d/%d' % tuple(r['改动'])))
    if hot_ex:
        print('\n  会画到图上的字段动过的 exhibit：%s' % '、'.join(hot_ex))
        print('  这些图必须重出、重新逐张看过、并重新签收。')
    if '--verbose' in sys.argv:
        for title, keys in (('新增', added), ('删除', removed), ('改动', changed)):
            if not keys:
                continue
            hot = [k for k in keys if is_plotted(k)]
            cold = [k for k in keys if not is_plotted(k)]
            print(f'\n{title} {len(keys)} 项 —— 其中会画到图上的 {len(hot)} 项')
            for k in hot[:40]:
                print(f'  ⚠ {k}: {a.get(k)!r} → {b.get(k)!r}')
            if len(hot) > 40:
                print(f'  … 另有 {len(hot)-40} 项')
            for k in cold[:40]:
                print(f'    {k}')
            if len(cold) > 40:
                print(f'    … 另有 {len(cold)-40} 项')
    else:
        print('\n  （要看字段级明细：approve.py --diff --verbose）')
    if not (added or removed or changed):
        print('账本与签收时逐字段一致。')
        return
    hot_all = [k for k in added + removed + changed if is_plotted(k)]
    print()
    if hot_all:
        print(f'✗ 有 {len(hot_all)} 个字段会画到图上 —— 必须重出图、重交清单、重签。')
        sys.exit(1)
    print('✓ 改动全在文字/派生字段,没有一个会画到图上。'
           '\n  图不用重出;仍然需要用户看一眼这些改动再 --sign 补记录。')


if __name__ == '__main__':
    if '--diff' in sys.argv:
        diff()
    elif '--sign' in sys.argv:
        sign()
    elif '--check' in sys.argv:
        check()
    else:
        sys.exit(__doc__)
