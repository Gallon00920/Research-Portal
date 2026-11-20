# -*- coding: utf-8 -*-
"""换季体检：扫出「本该随季度变、却写死成上一季」的东西。

Alex 2026-08-25 的问题:「下季度用新报告运行这个 skill,会不会有数据停留在这个季度,
比如文件名 你做成可变动的了吗」—— 这个脚本就是那个问题的机械答案。

**每季运行 skill 的第一件事就是跑它**(在 series.json 的 meta 更新之后、出图之前)。
不通过说明有地方还锁在上一季,出来的稿会是「新数据 + 旧期名」——
而且版面检查抓不到(文件名与页眉会一起错)。
"""
import io, json, os, re, sys

FILES = ['build_doc.py', 'build_s2.py', 'build_s3.py', 'build_s4.py',
         'build_s5.py', 'build_s6.py', 'build_s7.py', 'ca_compute.py',
         'broker_row.py', 'gen_contracts.py']

# 季度/月份字面量。注释、docstring、以及明确标注为历史沿革的行不算。
QLIT = re.compile(r"'[^']*?(\d[QH]\d\d|\d{4}Q\d|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[- ]\d\d|\d{2} YTD)[^']*?'")
DATELIT = re.compile(r"'\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec), 20\d\d'")

fails, warns, oks = [], [], []


def strip_comments(src):
    """去掉 # 注释与三引号块 —— 那里写「2026Q3 踩过…」是溯源,不是硬编码。"""
    src = re.sub(r'"""[\s\S]*?"""', '', src)
    src = re.sub(r"'''[\s\S]*?'''", '', src)
    return '\n'.join(re.sub(r'#.*$', '', ln) for ln in src.split('\n'))


def main():
    D = json.load(io.open('series.json', encoding='utf-8'))
    M = D['meta']

    # ── 1 账本 meta 是否齐 ──────────────────────────────────
    # ⛔ report_date **不在这个清单里** —— Alex 2026-08-26：「必须是 skill 运行的当日的时间」，
    #    出稿日由 build_doc 出稿时取 date.today()，账本里存字面量就是错的根源。
    #    反过来查：账本里**不许**再有 report_date。
    need = ['rq', 'periods', 'as_of', 'screen']
    miss = [k for k in need if not M.get(k)]
    if M.get('report_date'):
        fails.append('账本 meta 里又出现了 report_date —— ⛔ 出稿日必须出稿时取当天'
                     '（build_doc 用 date.today()），账本里存字面量跨一天就印错'
                     '（Alex 2026-08-26 已经指出过一次）。删掉它。')
    if miss:
        fails.append(f'账本 meta 缺字段 {miss} —— 正文要从这儿读季度/出稿日/期标签')
    else:
        oks.append(f"账本 meta 齐:rq={M['rq']}、"
                   f"periods={M['periods'].get('market_cq')}/{M['periods'].get('fund_cq')}")

    # ── 2 出图/出稿脚本里不许有季度字面量 ─────────────────────
    for f in FILES:
        if not os.path.exists(f):
            continue
        code = strip_comments(io.open(f, encoding='utf-8').read())
        hits = sorted(set(QLIT.findall(code)))
        dates = sorted(set(DATELIT.findall(code)))
        if f == 'broker_row.py':
            # 这是「本季 broker 名录」的录入脚本,内容本来就是本季的;只提醒别忘了重写
            if hits:
                warns.append(f'{f}: 含本季字面量 {hits[:6]} —— 这是逐季录入脚本,'
                             f'下季必须整份重写(不是改几个数)')
            continue
        if hits or dates:
            # 分级:出现在**格式化模板/表头/文件名**里的是硬错(会印出旧期名);
            #      出现在整句英文散文或源文件名里的是本季事实,每季重写正文时复核即可。
            hard, soft = [], []
            for lit in set(hits + dates):
                ctx = [ln.strip() for ln in code.split('\n') if lit in ln]
                looks_prose = any(len(c) > 60 and c.count(' ') > 8 for c in ctx)
                looks_fname = any(('.pdf' in c or '.xlsx' in c or '.json' in c) for c in ctx)
                (soft if (looks_prose or looks_fname) else hard).append(lit)
            if hard:
                fails.append(f'{f}: 期名标签写死了 {sorted(hard)[:8]} —— '
                             f'必须改成从 meta.rq / meta.periods 读')
            if soft:
                warns.append(f'{f}: 本季事实句或源文件名里含 {sorted(soft)[:8]} —— '
                             f'不是标签 bug,但**每季重写正文时必须逐句复核**')
            if not hard and not soft:
                oks.append(f'{f}: 无季度字面量')
        else:
            oks.append(f'{f}: 无季度字面量')

    # ── 2b 不许自己拼季度目录 / 写死上传路径 ─────────────────
    PATHLIT = re.compile(r"'/mnt/user-data/uploads/[^']*'|\"/mnt/user-data/uploads/[^\"]*\"")
    for f in FILES + ['pc_review_sheet.py', 'export_sources.py', 'src_audit.py',
                      'period_evidence.py', 'pc_period_check.py']:
        if not os.path.exists(f) or f == 'pcpaths.py':
            continue
        code = strip_comments(io.open(f, encoding='utf-8').read())
        bad_path = PATHLIT.findall(code)
        if bad_path:
            fails.append(f'{f}: 自己拼了上传路径 {bad_path[:2]} —— 一律走 pcpaths.quarter_dir() / '
                         f'pcpaths.one(<通配符>),季度由账本 meta.rq 推')

    # ── 2c 不许写死本季源文件全名(下季文件全换) ───────────────
    FNAME = re.compile(r"'[^']{6,}\.(?:pdf|xlsx|xls|docx)'")
    for f in FILES + ['src_audit.py', 'period_evidence.py']:
        if not os.path.exists(f):
            continue
        code = strip_comments(io.open(f, encoding='utf-8').read())
        names = [m.group(0) for m in FNAME.finditer(code)
                 if '*' not in m.group(0)              # 通配符取文件 = 正确写法
                 and '{' not in m.group(0)             # f-string 插了变量（如 {RQ}）
                 and '<' not in m.group(0)]            # <quarter> 这类占位
        if names and f != 'broker_row.py':
            fails.append(f'{f}: 写死了源文件全名 {names[:3]} —— 下季文件名会变,'
                         f'改成 pcpaths.one(\'<子目录>/<前缀>_*.xlsx\') 这种通配符')
        elif names:
            warns.append(f'{f}: 含源文件全名 {len(names)} 处 —— 逐季录入脚本,下季整份重写')

    # ── 2d RQ 必须是**运行季**,不是数据季 ─────────────────────
    #   Alex 2026-08-25:「文件名/标题/页眉的季度是 skill 运行时的季度。现在是 Q3,
    #   季报最新甚至只有 Q1,命名还得用运行季。这个要写死。」
    import datetime
    _t = datetime.date.today()
    run_q = f'{_t.year}Q{(_t.month - 1) // 3 + 1}'
    if M.get('rq') != run_q:
        warns.append(f"meta.rq={M.get('rq')} 与运行季 {run_q} 不同 —— "
                     f'如果是补做旧季度报告,这是对的;否则改成 {run_q}。'
                     f'⛔ 命名季度看**运行日**,不看数据走到哪一期。')
    else:
        oks.append(f'meta.rq={run_q} = 运行季(文件名/标题/页眉用它)')
    _ao = M.get('as_of') or {}
    _dq = [v.get('quarter') for v in _ao.values() if isinstance(v, dict) and v.get('quarter')]
    if _dq and M.get('rq') in _dq:
        warns.append(f"meta.rq={M.get('rq')} 与某个数据层的季度相同({_dq}) —— "
                     f'确认这不是把数据季当成了命名季')
    elif _dq:
        oks.append(f'命名季 {M.get("rq")} 与数据季 {_dq} 分开(数据滞后是正常的)')

    # ── 2e y 轴必须冻结在账本里,不许每季 autoscale ───────────
    E0 = D['exhibits']
    auto = re.compile(r'set_ylim\((?![^)]*ylim)[^)]*(?:max|nanmax|min)\(')
    leak = []
    for f in FILES:
        if not os.path.exists(f) or not f.startswith('build_s'):
            continue
        _lines = strip_comments(io.open(f, encoding='utf-8').read()).split('\n')
        # 两行式 autoscale：`top = np.nanmax(vals)` 在上面几行，`ax2.set_ylim(0, top*1.45)` 在这行。
        # 2026Q3 漏过一次（Ex 7 的右轴）：max() 不在 set_ylim 那一行上，单行正则看不见。
        for i, ln in enumerate(_lines, 1):
            m2 = re.search(r'set_ylim\(\s*0\s*,\s*([A-Za-z_]\w*)\s*\*', ln)
            # ⚠ 不能写 `'ylim' not in ln` —— `set_ylim` 本身就含 "ylim",这个守卫永远为真,
            #   于是整条检查静默失效(2026-08-25 实测到)。要查的是**有没有引用账本字段**。
            if m2 and 'ent[' not in ln and 'ent.get(' not in ln:
                _near = ' '.join(_lines[max(0, i - 5):i - 1])
                if "ent.get('ylim')" not in _near and "ent.get('rhs_ylim')" not in _near \
                   and "ent['ylim']" not in _near and "ent['rhs_ylim']" not in _near:
                    _back = ' '.join(_lines[max(0, i - 8):i - 1])
                    if re.search(r'\b' + re.escape(m2.group(1)) + r'\s*=[^=].*(max|nanmax|amax)\s*\(',
                                 _back):
                        leak.append(f'{f}:{i}(两行式)')
        for i, ln in enumerate(_lines, 1):
            if not auto.search(ln):
                continue
            # 前三行里出现 ent.get('ylim') / ('rhs_ylim') 说明这是 else 兜底,不算泄漏
            near = ' '.join(_lines[max(0, i - 4):i])
            if "ent.get('ylim')" in near or "ent.get('rhs_ylim')" in near:
                continue
            leak.append(f'{f}:{i}')
    if leak:
        warns.append(f'出图脚本里仍有按数据 autoscale 的 y 轴({len(leak)} 处:{leak[:4]})—— '
                     f'账本给了 ylim 就必须优先用它。y 轴每季跟着数据变,'
                     f'同一张图的曲线形状跨季就对不上(OTF 02_quarter_window §3.5.1)')
    else:
        oks.append('出图脚本没有按数据 autoscale 的 y 轴')

    # ── 3 meta 与账本实际末期是否自洽 ───────────────────────
    E = D['exhibits']
    pag = (E.get('fund_pag_kpi_qoq') or {}).get('periods')
    if pag and M.get('periods', {}).get('fund_cq') != pag[-1]:
        fails.append(f"meta.periods.fund_cq={M['periods'].get('fund_cq')} 与基金表末期 {pag[-1]} 不一致")
    elif pag:
        oks.append(f'meta.periods.fund_cq 与基金表末期一致({pag[-1]})')

    # ── 4 上一季的产物有没有混进共用目录 ───────────────────
    #    (只在能看到 _charts 目录时查;在容器里跑通常看不到,跳过)
    oks.append('目录约定见 SKILL 铁律一:_charts\\ 只放 series.json 与冻结的外部原始文件')

    print(f"\n=== 换季体检 · {M.get('rq')} ===\n")
    for m in oks:
        print('  ✓', m)
    for m in warns:
        print('  ?', m)
    for m in fails:
        print('  ✗', m)
    print(f'\n通过 {len(oks)}　不通过 {len(fails)}　待确认 {len(warns)}')
    if fails:
        print('\n不通过就别往下跑 —— 这类错出来的稿是「新数据配旧期名」,版面检查抓不到。')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
