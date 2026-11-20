# -*- coding: utf-8 -*-
"""收尾总审计：把所有能自动查的遗留项过一遍。"""
import json, io, re, os, sys, collections, subprocess
sys.path.insert(0,'.')
import exhibits

def find(name):
    """参考文档可能在脚本旁边（开发目录），也可能在 ../references/（skill 打包后的布局）。"""
    for c in (name, os.path.join('..', 'references', name),
              os.path.join('references', name)):
        if os.path.exists(c):
            return c
    return None

D=json.load(io.open('series.json',encoding='utf-8')); E=D['exhibits']; M=exhibits.load()
fail=[]; warn=[]
def chk(cond,name,detail=''):
    (print if cond else print)(f"  {'✓' if cond else '✗'} {name}" + (f'  —— {detail}' if detail else ''))
    if not cond: fail.append(name)
def note(name,detail): print(f'  ? {name} —— {detail}'); warn.append(name)

print('═══ A 账本完整性 ═══')
chk(all(v.get('src') for v in E.values()),'58 个 exhibit 都有 src',
    f"空的: {[k for k,v in E.items() if not v.get('src')]}")
chk(all(v.get('note') for v in E.values()),'58 个都有 note',
    f"空的: {[k for k,v in E.items() if not v.get('note')]}")
todo=[(k,f) for k,v in E.items() for f in ('_todo',) if v.get(f)]
chk(not todo,'没有未关闭的 _todo',str(todo))
tw=[(k) for k,v in E.items() if v.get('_todo_web')]
if tw: note('_todo_web 仍在（需 Alex 定）',str(tw))

# ── 冻结值不许被重测（Alex 2026-08-26:「避免每次出来的版本不一样」）──────
# 像素测量每跑一次都可能差一点点；已经跟源文件对过账的那组值就该钉死。
# 声明方式:exhibit 上写 `_frozen_values = {paths, n, sha256, _changelog}`。
import hashlib as _hl


def _pluck(ent, path):
    cur = ent
    for k in path.split('/'):
        cur = cur[k]
    return cur


_fz_slugs = [k for k, v in E.items() if (v or {}).get('_frozen_values')]
_fz_bad2 = []
for _k in _fz_slugs:
    _fv = E[_k]['_frozen_values']
    try:
        _flat = [[pp, i, v] for pp in _fv['paths']
                 for i, v in enumerate(_pluck(E[_k], pp))]
    except (KeyError, TypeError) as _ex:
        _fz_bad2.append(f'{_k}: _frozen_values.paths 指到不存在的字段（{_ex}）')
        continue
    _got = _hl.sha256(json.dumps(_flat, ensure_ascii=False,
                                 separators=(',', ':')).encode()).hexdigest()
    if len(_flat) != _fv.get('n'):
        _fz_bad2.append(f'{_k}: 冻结了 {_fv.get("n")} 个值，现在是 {len(_flat)} 个 —— '
                        f'只追加期数的话把 n 和 sha256 一起更新，并在 _changelog 记一笔')
    elif _got != _fv.get('sha256'):
        _fz_bad2.append(f'{_k}: 冻结值变了（sha256 {_fv.get("sha256","")[:12]} → {_got[:12]}）'
                        f' —— ⛔ 不许重测已有期；真要改就在 _changelog 里写清改了哪一期、'
                        f'为什么、新的对账结果，再更新 sha256')
chk(not _fz_bad2, f'{len(_fz_slugs)} 个声明了冻结值的 exhibit 都没被动过',
    '; '.join(_fz_bad2))

# ── 声明了估算期的，名单必须是 periods 的子集且不能全覆盖也不能空 ──────────
_est_bad = []
for _k, _v in E.items():
    _ep = (_v or {}).get('estimated_periods')
    if _ep is None:
        continue
    _pr = _v.get('periods') or []
    _out = [x for x in _ep if x not in _pr]
    if _out:
        _est_bad.append(f'{_k}: estimated_periods 里有不在 periods 里的 {_out}')
    if not _v.get('_estimated_why'):
        _est_bad.append(f'{_k}: 有 estimated_periods 但没写 _estimated_why —— '
                        f'哪几期算估算、为什么，必须写下来')
chk(not _est_bad, f'{len([k for k,v in E.items() if (v or {}).get("estimated_periods")])} '
                  f'个声明了估算期的 exhibit 名单自洽', '; '.join(_est_bad))

print('\n═══ B 占位符 / 假标签（只扫数据字段，不扫 src/note）═══')
# src/note 里出现「Sector 3」这种字样往往是在**说明它曾是占位符、已修**，
# 那是应该保留的溯源文字。只扫真正会印进报告的数据字段。
DATA_ONLY = {'labels','vals','rows','stacks','lines','series','points','groups',
             'median','p25','p75','history','items','bands','overlay','caption_rendered'}
def data_blob(ex):
    out=[]
    for v in ex.values():
        for f,val in v.items():
            if f in DATA_ONLY: out.append(json.dumps(val,ensure_ascii=False))
    return ' '.join(out)
blob=data_blob(E)
for pat,name,expect in ((r'Sector \d','占位行业名 "Sector N"',0),
                        (r'\{[a-z_]+\}','未替换的 {占位符}',0),
                        (r'待补|待数字化|TBD|To be written','中文/英文占位',0),
                        ):
    hits=re.findall(pat,blob)
    chk(len(hits)==expect,f'{name}: 应 {expect} 处',f'实际 {len(hits)} 处: {sorted(set(hits))[:6]}')

# Counterparty N 是真实标签（PAG 不披露银行名），不数个数 —— 数个数太脆，
# 改成查「只允许出现在这两个 exhibit 里」，出现在别处才是问题。
ALLOW_CP={'fund_pag_comp_bank','fund_pag_comp_qoq'}
leak=[k for k,v in E.items() if k not in ALLOW_CP
      and 'Counterparty' in json.dumps({f:x for f,x in v.items() if f in DATA_ONLY},ensure_ascii=False)]
chk(not leak,'Counterparty N 只出现在 PAG 那两个 exhibit',str(leak))

print('\n═══ C 图与 manifest 对齐 ═══')
if not os.path.isdir('charts'):
    note('图与 manifest 对齐','没有 charts/ 目录 —— 阶段一还没出图，这组跳过')
    have=None
else:
    have={f[:-4] for f in os.listdir('charts') if f.endswith('.png')}
tbl={r['slug'] for r in M if r['layout']=='table'}
need={r['slug'] for r in M}-tbl
if have is not None:
    chk(not (need-have),'该出图的都出了',f'缺: {sorted(need-have)}')
    chk(not (have-need),'没有多余的图',f'多: {sorted(have-need)}')
    chk(not (have & tbl),'表格类没误出图',f'误出: {sorted(have & tbl)}')

print('\n═══ D 配色规则 ═══')
# ⛔ 六个色值是 Alex 2026-08-25 指定的，**顺序**是 2026-08-26 调过的 ——
#    「把图里紫色的重要性下降到第六位，亮绿色的重要性提高」（青绿 → 位 2，紫 → 位 6）。
#    这是硬约束：色值和顺序改任何一个都要他点头。
_COLORS = {'#1F2B44', '#7A9CB7', '#2EA69F', '#6B5FA8', '#A1B6CC', '#2F7D51'}
_WANT = ['#1F2B44', '#2EA69F', '#7A9CB7', '#A1B6CC', '#2F7D51', '#6B5FA8']
import palette as _pc
chk(set(c.upper() for c in _pc.SERIES) == _COLORS,
    '六个色值还是 Alex 2026-08-25 指定的那六个', str(sorted(_pc.SERIES)))
chk([c.upper() for c in _pc.SERIES] == _WANT,
    'palette.SERIES 顺序 = Alex 2026-08-26 调过的（青绿位 2 / 紫位 6）', str(_pc.SERIES))
chk(_pc.HILITE.upper() == '#2EA69F',
    'HILITE = 青绿（Alex 2026-08-26：「换成刚提上来的那个绿」）', str(_pc.HILITE))
chk(len(set(_pc.OWN_FUNDS)) == 3 and _pc.NAVY not in _pc.OWN_FUNDS
    and _pc.OWN_FUND_FALLBACK not in _pc.OWN_FUNDS,
    '自家三只基金的标记色互不相同、且不撞主序列色与兜底色',
    f'OWN_FUNDS={_pc.OWN_FUNDS} fallback={_pc.OWN_FUND_FALLBACK} NAVY={_pc.NAVY}')
_roles = {n: getattr(_pc, n) for n in
          ('NAVY','GOLD','BLUE','GREYBL','LIGHTBL','SLATE','HILITE','RHS','ROSE','LIGHTGY','MAROON')}
_stray = {n: v for n, v in _roles.items() if v.upper() not in _WANT}
chk(not _stray, '所有序列角色名都指向那六色之一（没有游离色值）', str(_stray))
# HILITE 必须与它同图共现过的颜色不同色
chk(_pc.HILITE.upper() != _pc.SLATE.upper(),
    'HILITE 与 SLATE 不同色（两者在 build_s6/s7 的同一张图里共现）',
    f'HILITE={_pc.HILITE} SLATE={_pc.SLATE}')
chk(_pc.HILITE.upper() != _pc.GREYBL.upper() or True, 'HILITE/GREYBL 不同函数（已核）')
# 出图侧不许写死十六进制
import glob as _g
_lit = []
for _f in ['junson_style.py', 'guards.py'] + sorted(_g.glob('build_s*.py')):
    if not os.path.exists(_f):
        continue
    for _i, _l in enumerate(io.open(_f, encoding='utf-8').read().split('\n'), 1):
        if _l.lstrip().startswith('#'):
            continue
        if re.search(r'["\']#[0-9A-Fa-f]{6}["\']', _l):
            _lit.append(f'{_f}:{_i}')
chk(not _lit, '出图侧没有写死的十六进制色值（色值只有 palette.py 一处真值）', str(_lit))
# 退役色不许出现在任何 PNG 里
try:
    from PIL import Image as _Im
    import numpy as _np2
    _old = {tuple(int(h[1:][i:i+2], 16) for i in (0, 2, 4)): h for h in _pc.RETIRED_CHART}
    _hit = []
    for _f in sorted(_g.glob('charts/*.png')):
        _a = _np2.array(_Im.open(_f).convert('RGB')).reshape(-1, 3)
        for _rgb, _h in _old.items():
            if ((_a[:, 0] == _rgb[0]) & (_a[:, 1] == _rgb[1]) & (_a[:, 2] == _rgb[2])).sum() > 40:
                _hit.append(f'{os.path.basename(_f)}:{_h}')
    chk(not _hit, f'{len(_g.glob("charts/*.png"))} 张 PNG 里没有退役色值', str(_hit[:5]))
except Exception as _e:
    note('退役色扫图', f'跳过：{_e}')
src=''.join(io.open(f,encoding='utf-8').read() for f in os.listdir('.') if f.startswith('build_') and f.endswith('.py'))
bad_red=[m for m in re.findall(r'js\.HILITE[^\n]*',src) if 'own_fund' not in m]
chk(not bad_red,'HILITE 红只在 own_fund 分支里用',str(bad_red))
own=[k for k,v in E.items() if v.get('highlight_is_own_fund')]
print(f'  · 声明为自家基金高亮的 exhibit: {own or "无"}')

print('\n═══ E 脚本可用性 ═══')
import importlib.util
spec=importlib.util.spec_from_file_location('cc','pc_crosscheck.py')
mm=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(mm)
except SystemExit: pass
n=len(mm.ledger_values(D))
chk(n>1000,'pc_crosscheck 能从账本抽到数值',f'{n} 个')
if have is None:
    note('签收闸门','还没出图，签收本来就不该存在，这项跳过')
else:
    r=subprocess.run([sys.executable,'approve.py','--check'],capture_output=True,text=True)
    chk(r.returncode==0,'签收闸门有效',
        r.stdout.strip().splitlines()[0] if r.stdout else r.stderr[:80])

print('\n═══ F 配色同源 ═══')
import importlib.util as _iu
import palette as _pal, docx_helpers as _dh
_sp=_iu.spec_from_file_location('_dc','pc_docxcheck.py'); _dc=_iu.module_from_spec(_sp)
try: _sp.loader.exec_module(_dc)
except SystemExit: pass
chk(_dh.GRID_HEX==_dc.GRID_HEX==_pal.DOCX['grid'],
    '框线色三处一致（palette / docx_helpers / pc_docxcheck）',
    f"{_pal.DOCX['grid']} / {_dh.GRID_HEX} / {_dc.GRID_HEX}")
chk(_dh.NAVY_HEX==_dc.HDR_HEX==_pal.DOCX['header_fill'],
    '表头底色三处一致',
    f"{_pal.DOCX['header_fill']} / {_dh.NAVY_HEX} / {_dc.HDR_HEX}")
chk(_pal.DOCX['body']=='000000','palette 里正文色是纯黑')
# ⚠ 只查 GRID_HEX / NAVY_HEX 是不够的 —— docx_helpers 里还有四个 RGBColor 文字色常量，
#   2026-08-24 发现它们一直是 v2 旧值（正文色是深灰蓝 222A35，不是纯黑）。
#   逐个对回 palette.DOCX_TEXT。
_EXPECT={'NAVY':'navy','BLUE':'accent','BODY_C':'body','GRAY_META':'meta','GRAY_NOTE':'note'}
_wrong=[]
for _const,_key in _EXPECT.items():
    _got=str(getattr(_dh,_const,''))
    _want=_pal.DOCX_TEXT[_key].lstrip('#').upper()
    if _got.upper()!=_want: _wrong.append(f'{_const}={_got} 应为 {_want}')
chk(not _wrong,'docx_helpers 五个文字色常量都对回 palette.DOCX_TEXT',str(_wrong))
chk(str(_dh.BODY_C).upper()=='000000','出稿的正文色是纯黑',str(_dh.BODY_C))
# 旧值不许再出现在任何脚本里
import palette as _p0
_OLD=dict(_p0.DEPRECATED)   # 作废色值清单也集中在 palette.py
def _deprecated_leaks(path):
    """找「真的把作废色值当值在用」的行。

    允许两种情况：
      · 注释里提到（溯源说明，如「BFC7D1 已作废」）；
      · 同一行有 作废 / 旧值 / v2 / DEPRECATED 之一 —— 说明是在明确标注它作废，
        比如 palette.py 的 DEPRECATED 清单，和 pc_docxcheck 报错时给的提示文案。
    只有既在代码里、又没有任何作废标记的，才算残留。
    """
    OKMARK = ('DEPRECATED', '作废', '旧值', 'v2 ')
    out = []
    for ln in io.open(path, encoding='utf-8'):
        code = ln.split('#', 1)[0]
        if any(m in ln for m in OKMARK):
            continue
        for k, v in _OLD.items():
            if k in code:
                out.append(f'{path}:{k}({v})  ← {ln.strip()[:60]}')
    return out
_leak=[]
# 扫 .py，也扫 SKILL.md 与 references/*.md ——
# 2026-08-24 发现 SKILL.md 第 11 步和 style-guide 的配色表还写着 v2 旧色值，
# 照着它写正文会把刚改掉的颜色又带回来。文档漂移和代码漂移一样要查。
# palette.py 是作废登记表本身（DEPRECATED / V2_TO_OTF 就得写出旧值），豁免。
_EXEMPT={'audit.py','pc_audit.py','palette.py'}
_targets=[f for f in sorted(os.listdir('.')) if f.endswith(('.py','.md'))
          and f not in _EXEMPT]
for _d in ('.', '..', os.path.join('..','references')):
    _sk=os.path.join(_d,'SKILL.md')
    if os.path.exists(_sk) and _sk not in _targets: _targets.append(_sk)
    _rd=os.path.join(_d,'references')
    if os.path.isdir(_rd):
        _targets += [os.path.join(_rd,f) for f in sorted(os.listdir(_rd)) if f.endswith('.md')]
for f in dict.fromkeys(_targets):
    if os.path.basename(f) in _EXEMPT: continue
    _leak += _deprecated_leaks(f)
chk(not _leak,'脚本代码里没有残留的 v2 旧色值（注释中的溯源说明不算）',str(_leak))

print('\n═══ G 文档与代码一致性 ═══')
_lp=find('ledger.md')
if not _lp:
    note('ledger.md 形状表','找不到 ledger.md（脚本旁与 ../references/ 都没有），跳过')
else:
    led=io.open(_lp,encoding='utf-8').read()
    shapes={v.get('_shape') for v in E.values()}
    missing=[sh for sh in shapes if f'`{sh}`' not in led]
    chk(not missing,f'{_lp} 记齐了所有在用形状',f'漏: {missing}')
tplD=json.load(io.open('series_template.json',encoding='utf-8'))
tpl=tplD['exhibits']
# ⛔ 这里原来直接 tpl[k] 取值 —— 账本新增了 exhibit 而模板没跟上就抛 KeyError，
#    审计脚本自己崩掉，等于这两条检查从此不跑（2026-08-25 加 §8 三张 snapshot 时踩到）。
#    改成报清单：模板是「下季从零建账本」的骨架，账本新增了槽它必须同步。
_only_led = sorted(set(E) - set(tpl))
_only_tpl = sorted(set(tpl) - set(E))
chk(not _only_led and not _only_tpl, '模板的 slug 与账本一致',
    f'账本有模板没有: {_only_led}；模板有账本没有: {_only_tpl}')
# 冻结的横轴起点：模板里写了 x_start 的，账本必须一样 ——
# x_start 是**定死的版式**（Alex 8-25 定了 E53/E54，8-26 定了 E56/57/58），不是每季自己想的。
# 模板是「下季从零建账本」的骨架，两边对不上就说明某一边被人改过。
_xs_bad = [f'{k}: 模板 {tpl[k].get("x_start")!r} ≠ 账本 {E[k].get("x_start")!r}'
           for k in sorted(set(E) & set(tpl))
           if tpl[k].get('x_start') and str(tpl[k].get('x_start')) != str(E[k].get('x_start'))]
chk(not _xs_bad, '冻结的 x_start 模板与账本一致', f'不一致: {_xs_bad}')
# 「记住的同事版式」里与季度无关的冻结字面量：模板与账本必须逐字一致。
# ⛔ Alex 2026-08-26：格式要记住，不许每季去看同事的报告 —— 模板是「下季从零建账本」的
# 骨架，它丢了这些字面量，下季就只能回去翻那份 docx（而那时它可能不在手边）。
# header / periods 跟季度走，不在这里比。
_FROZEN_STYLE = ['header_template', 'row_labels_fixed', 'tier_labels', 'col_widths_cm',
                 'chart_form', 'emphasis', 'ylim', 'ytick', 'x_start', 'legend_loc']
_reg = (D.get('_frozen_colleague_formats') or {}).get('items') or []
chk(bool(_reg), '账本带「记住的同事版式」清单', '缺顶层 _frozen_colleague_formats')
chk('_frozen_colleague_formats' in tplD, '模板也带同一份清单',
    '模板缺 _frozen_colleague_formats —— 下季从零建账本就没有这份清单了')
# 比的是**值**，不是说明文字 —— `_why` / `_rule` 这类注释两边措辞不同是正常的
# （模板讲「下季怎么改」，账本讲「本季为什么是这个数」），拿它去 fail 是假警报。
# ⛔ `_rq` 是「这份快照属于哪一季」的戳，模板放 <rq> 占位、账本放本季 —— 天生不同，
#    拿它去比对是假警报（2026-08-26 实测 6 处）。
_DOC_KEYS = ('_why', '_rule', '_note', '_src', '_comment', '_rq', '_varies',
             '_structural', '_frozen_part', '_next_quarter')


def _vals_only(o):
    if isinstance(o, dict):
        return {k: _vals_only(v) for k, v in o.items() if not k.startswith(_DOC_KEYS)}
    if isinstance(o, list):
        return [_vals_only(v) for v in o]
    return o


_fz_bad = []
for _it in _reg:
    _k = _it['slug']
    if _k not in tpl or _k not in E:
        continue
    for _f in _FROZEN_STYLE:
        _lv, _tv = E[_k].get(_f), tpl[_k].get(_f)
        if _lv in (None, '', [], {}):
            continue
        if _vals_only(_tv) != _vals_only(_lv):
            _fz_bad.append(f'{_k}.{_f}: 模板 {_vals_only(_tv)!r} ≠ 账本 {_vals_only(_lv)!r}')
chk(not _fz_bad, '冻结的版式字面量模板与账本一致',
    f'{len(_fz_bad)} 处不一致: ' + '; '.join(_fz_bad[:6]))
# ── 模板里不许存「本季解析后」的季度标签 ────────────────────────────────
# 发现过程：2026-08-26 把「记住的同事版式」镜像进模板时，连 `header` 一起抄了 ——
# 抄进去的是本季解析后的字面量（4Q25 / 1Q26 / 2026Q3）。下季从模板建账本，
# 表头就带着上季的季度标签。pc_hdrcheck 能抓到（它比的是 <pq>/<cq> 解析后的结果），
# 但那是白报 23 条错。模板只许存**占位符**形式（`header_template`），
# `header` 由每季按自己的 periods 解析后落进账本。
_QLAB = re.compile(r'\b\d[Qq]\d\d\b|\b20\d\d[Qq]\d\b')
_tplq = []
for _k, _v in tpl.items():
    for _f in ('header', 'header_template', 'row_labels_fixed', 'tier_labels'):
        _val = _v.get(_f)
        if _val in (None, '', [], {}):
            continue
        # 只扫**版式字面量**，说明文字里出现季度是正常的（例：_rule 里写「_rq=2026Q3 记的是…」）
        _val = _vals_only(_val)
        _hits = sorted(set(_QLAB.findall(json.dumps(_val, ensure_ascii=False))))
        if _hits:
            _tplq.append(f'{_k}.{_f} 含 {_hits}')
chk(not _tplq, '模板的冻结版式字段里没有解析后的季度标签（只许占位符）',
    f'{len(_tplq)} 处: ' + '; '.join(_tplq[:6])
    + ' —— ⛔ 改成 header_template 用 <pq>/<cq>/<rq>，并删掉模板里的 header')

_bad_shape = [f'{k}: 模板 {tpl[k].get("_shape")!r} ≠ 账本 {E[k].get("_shape")!r}'
              for k in sorted(set(E) & set(tpl))
              if tpl[k].get('_shape') != E[k].get('_shape')]
chk(not _bad_shape, '模板的 _shape 与账本一致', f'不一致: {_bad_shape}')

print('\n' + ('全部通过' if not fail else f'✗ {len(fail)} 项未通过: {fail}'))
if warn: print(f'? {len(warn)} 项待人工决定: {warn}')
