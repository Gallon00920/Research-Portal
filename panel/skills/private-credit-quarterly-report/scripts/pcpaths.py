# -*- coding: utf-8 -*-
"""路径与季度的唯一解析入口。

⛔ Alex 2026-08-25：「怎么能写死呢？下个季度东西都在下个季度的文件夹里啊，比如 2026Q4。」

**任何脚本都不许自己拼季度目录、不许写 '2026Q3' 这种字面量。**
季度只有一个真值源:`series.json` 的 `meta.rq`;目录一律由这里推。

    import pcpaths as P
    P.RQ            # '2026Q4'
    P.quarter_dir() # 本季源文件夹(暂存后的绝对路径)
    P.charts_dir()  # 出图目录
    P.ledger_path() # 账本
"""
import io, json, os, glob

LEDGER = os.environ.get('PC_LEDGER', 'series.json')


def _meta():
    return json.load(io.open(LEDGER, encoding='utf-8'))['meta']


def rq():
    """本季标签,如 2026Q4 —— 唯一真值源是账本 meta.rq。"""
    q = _meta().get('rq')
    if not q:
        raise SystemExit(f'✗ {LEDGER} 的 meta.rq 是空的 —— 先把本季标签写进账本,'
                         f'季度是所有路径与期名的唯一真值源。')
    return q


RQ = rq() if os.path.exists(LEDGER) else None

# 暂存根目录:device_stage_files 把设备上的文件夹放到这里
UPLOADS = os.environ.get('PC_UPLOADS', '/mnt/user-data/uploads')


def quarter_dir(q=None):
    """本季源文件夹。找不到就报错并列出实际有哪些季度目录 —— 绝不静默退回上一季。"""
    q = q or rq()
    cand = [os.path.join(UPLOADS, q),
            os.path.join(UPLOADS, 'Private Credit', q)]
    for c in cand:
        if os.path.isdir(c):
            return c
    seen = sorted(os.path.basename(p) for p in glob.glob(os.path.join(UPLOADS, '*'))
                  if os.path.isdir(p))
    raise SystemExit(f'✗ 找不到本季源文件夹({q})。找过:{cand}\n'
                     f'  暂存目录里现有:{seen}\n'
                     f'  先用 device_stage_files 把 {q} 文件夹暂存进来,'
                     f'⛔ 不许改用别的季度顶上。')


def sub(name, q=None):
    """本季某个子目录,如 sub('Competitor')。"""
    return os.path.join(quarter_dir(q), name)


def one(pattern, q=None, what=''):
    """在本季文件夹里按通配符找**唯一**一个文件。零个或多个都报错。

    下季文件名一定会变(带日期、带季度),所以取文件一律用模式匹配,不写全名。
        one('Competitor/PitchBook_Search_Result_Columns_*.xlsx')
    """
    hits = sorted(glob.glob(os.path.join(quarter_dir(q), pattern)))
    if not hits:
        raise SystemExit(f'✗ 本季文件夹里没有匹配 {pattern} 的文件{("（" + what + "）") if what else ""}。'
                         f'\n  确认这份料本季是否提供;缺料要显式标 not updated,不许拿上季的顶。')
    if len(hits) > 1:
        raise SystemExit(f'✗ {pattern} 匹配到多个:{[os.path.basename(h) for h in hits]}\n'
                         f'  把模式写得更准,或先清理文件夹 —— 不许随便挑一个。')
    return hits[0]


def charts_dir():
    d = os.environ.get('PC_CHARTS', 'charts')
    os.makedirs(d, exist_ok=True)
    return d


def out_dir():
    d = os.environ.get('PC_OUT', 'out')
    os.makedirs(d, exist_ok=True)
    return d


def ledger_path():
    return LEDGER


def report_name(ver=None):
    """成稿文件名 —— 季度来自账本,不许手打。"""
    v = ver or os.environ.get('PC_DOC_VER', '3')
    return os.path.join(out_dir(), f'Junson_Private_Credit_Report_{rq()}_EN_v{v}.docx')

# ─────────────────────────────────────────────────────────────────────────
# 交付落点(设备侧)—— ⛔ Alex 2026-08-25:「后续我们这里再生成报告 放到这个文件夹下,
# 不然太乱了」:…\04 Research\Private Credit\Test
#
# 成稿与它的来源清单一律写进 <PC 根>\Test\,不再往 <PC 根>\ 根目录扔。
# ⛔ 但账本与快照的位置**不变**(铁律一):
#     账本      <PC 根>\_charts\series.json        跨季共用
#     本季留痕  <PC 根>\<Q>\_charts_snapshot\      随季度走
# 这三个落点互不替代,别把账本也塞进 Test。
# ─────────────────────────────────────────────────────────────────────────
DELIVER_SUBDIR = 'Test'          # 相对 <PC 根>
LEDGER_SUBDIR  = '_charts'       # 相对 <PC 根>,跨季共用
SNAPSHOT_SUBDIR = '_charts_snapshot'   # 相对 <PC 根>\<Q>\


def deliver_targets(pc_root, ver=None):
    """给 device_commit_files 用的落点清单 —— 季度从账本读,路径不许手打。

        >>> deliver_targets(r'C:\...\04 Research\Private Credit')
        {'report': r'...\Private Credit\Test\Junson_Private_Credit_Report_2026Q4_EN_v1.docx',
         'sources': r'...\Private Credit\Test\sources_ledger_2026Q4.md',
         'ledger':  r'...\Private Credit\_charts\series.json'}
    """
    q = rq()
    v = ver or os.environ.get('PC_DOC_VER', '1')
    sep = '\\' if ('\\' in pc_root or ':' in pc_root) else '/'
    j = lambda *p: sep.join([pc_root.rstrip('/\\')] + list(p))
    return {
        'report':  j(DELIVER_SUBDIR, f'Junson_Private_Credit_Report_{q}_EN_v{v}.docx'),
        'sources': j(DELIVER_SUBDIR, f'sources_ledger_{q}.md'),
        'ledger':  j(LEDGER_SUBDIR, 'series.json'),
        'snapshot_dir': j(q, SNAPSHOT_SUBDIR),
    }
