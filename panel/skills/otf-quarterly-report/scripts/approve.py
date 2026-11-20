#!/usr/bin/env python3
"""阶段一的签收闸门。阶段二没有它就不许启动。

  python3 approve.py --sign     阶段一跑完、用户校对通过后落签收
  python3 approve.py --check    阶段二启动前校验（exit 0 通过 / 1 拒绝）

签收文件记 CQ、每张图的 sha256、series.json 的 sha256。
只要有任何一张图被重出、或账本被改过，校验就失败 —— 必须重新校对再签。
这样跨会话也成立：阶段二可以是全新一次会话。
"""
import hashlib, json, os, sys, glob

OUT = 'out'
SER = 'series.json'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def cq():
    return json.load(open(SER, encoding='utf-8'))['meta']['cq']


def tag(c):
    return c.replace("'", '').replace(' ', '')


def path_for(c):
    return f'APPROVED_{tag(c)}.json'


def manifest():
    files = sorted(glob.glob(os.path.join(OUT, '*.png')))
    return {os.path.basename(p): sha(p) for p in files}


def sign():
    c = cq()
    m = manifest()
    if not m:
        sys.exit(f'{OUT}/ 里没有 PNG，阶段一还没跑完')
    rec = {'cq': c, 'series_sha256': sha(SER), 'files': m, 'count': len(m)}
    json.dump(rec, open(path_for(c), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'[signed] {path_for(c)}  CQ={c}  {len(m)} 张图')
    print('阶段二现在可以启动（可以是新会话）。')


def check():
    c = cq()
    p = path_for(c)
    if not os.path.exists(p):
        sys.exit(f'✗ 拒绝启动阶段二：没有 {p}。\n'
                 f'  阶段一必须先跑完、把 22 张图和核对清单交给用户逐项校对、'
                 f'用户确认后才能 approve.py --sign。\n'
                 f'  不许跳过这一步用默认值往下走 —— 定时任务场景下也必须停在这里。')
    rec = json.load(open(p, encoding='utf-8'))
    bad = []
    if rec.get('cq') != c:
        bad.append(f'签收的 CQ 是 {rec.get("cq")}，账本现在是 {c}')
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
                 + '\n  改动过的部分要重新交给用户校对，再 approve.py --sign。')
    print(f'✓ 签收有效：CQ={c}，{rec["count"]} 张图，账本未变。阶段二可以开始。')


if __name__ == '__main__':
    if '--sign' in sys.argv:
        sign()
    elif '--check' in sys.argv:
        check()
    else:
        sys.exit(__doc__)
