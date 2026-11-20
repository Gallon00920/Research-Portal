# 账本 · `series.json`

## 它是什么

58 个 exhibit 的**每一个数据点 + 每个点的出处**。这套东西的心脏。

```
exhibit = junson_style.py（样式，定稿后不改） × series.json 的切片（数据，只追加）
```

**放在 `<父目录>\_charts\`，与各季度文件夹平级，跨季共用。**
不要放进任何一季的文件夹 —— 那一季归档了账本就跟着走了；也不要每季复制一份 —— 会分叉成两本账。

## 为什么必须有

没有账本会出三件事，都不是理论风险:

1. **历史点会漂。** `mkt_aum_by_channel` 是 2015 至今的年度序列，其中 retail / insurance
   那两条是**从源图上读的近似值**。每季重读一遍，2015 年的数字这季和下季就不一样，
   而且读者不会发现。冻结之后只追加最新一年。
2. **基金 QoQ 表需要两个季度的报告。** 组合 QoQ（`fund_*_comp_qoq`）和 KPI 环比
   （`fund_pag_kpi_qoq`）都要上季的数。账本记住了，本季就只需要放进**三份新报告**。
3. **正文和图会对不上。** 正文若为了写作再抽一遍数，图上写 2.8%、正文写 2.9%，
   两处各自自洽，通读根本发现不了。规则:**凡 exhibit 上出现过的数，正文一律从账本读。**

## key 是稳定 slug，不是 exhibit 编号

编号每季会变（增删一张图，后面全要重排）。slug 不会。

- `exhibit_manifest.json` —— 唯一定义文档顺序的地方
- `exhibits.py` —— 从 manifest 推编号、生成题注、把正文里的 `{{ex:slug}}` 换成 `Exhibit N`

**正文里绝不手写编号。** 58 个手工维护，第二季必错。

## 结构

```json
{
  "meta": {
    "rq": "2026Q4",
    "as_of": {
      "market":     {"quarter": "3Q26"},
      "fund":       {"quarter": "2Q26"},
      "competitor": {"export_date": "2026-11-12"}
    },
    "screen": {"universe_fund_count": 341, "definition": "North America direct lending drawdown funds"},
    "comparator_set": {"upper_mm": ["KKR","Ares","Apollo"],
                       "core_mm": ["TPG Twin Brook","Golub","HarbourVest","Oaktree"]},
    "vintage_convention": {"PAG_BRS_III": 2023, "Guggenheim_PDF_IV": 2024, "HSBC_RCF": 2024},
    "cohorts": {"2023": {"n_irr": 26, "median_irr": 10.7, "iqr_irr_pp": 4.6}, ...}
  },
  "exhibits": {
    "<slug>": {
      "_shape": "series_stacked",     // 决定恒等式怎么查，见下表
      "_section": "2.2",
      "_layout": "pairL",
      "_as_of_block": "market",       // market / fund / competitor
      "src": "……",                    // 图级来源，必填
      "window_max": null,             // null = 不裁；数字 = 最多保留几期
      "note": "……",                   // 图下 Note: 的内容
      "caption_rendered": "……",       // 动态题注本季渲染成什么（15 个动态题注必填）
      "...形状对应的数据字段..."
    }
  }
}
```

### 十五种形状

2026Q3 实跑之后从十种扩到十五种。新增的五种都是研报里真实存在但原来没有对应形状的图形，
`pc_review_sheet.py` 的明细行输出和恒等式都已支持；`series_template.json` 是从真账本反向生成的，
每个 slug 的 `_shape` 与流水线一致。

| `_shape` | 数据字段 | 恒等式 |
|---|---|---|
| `series_stacked` | `periods` `stacks{}` `rhs_line` `ylim` `ytick` | 每期分项之和 = 总计（若给了 total）|
| `series_lines` | `periods` `lines{}` `rhs_line` `ylim` `ytick` | 期数与各线长度一致 |
| `series_grouped` | `periods` `stacks{}`（时序分组柱）| 各组长度 = 期数 |
| `groups_stacked` | `groups[]` `periods[]` `stacks{}`（值按 groups×periods 行优先展平）| **每根柱子加总 = 100%** |
| `groups_bars` | `groups[]` `series{年份:[各组值]}`，`None` = 未披露 | 各系列长度 = 组数；`None` 不许当 0 |
| `shares` | `labels[]` `vals[]` `panels` | **加总 = 100%**（多面板逐面板查）|
| `bars_categorical` | `labels[]` `vals[]` `highlight` | 长度一致 |
| `bars_grouped_categorical` | `labels[]` `series{系列:[各类别值]}` | 各系列长度 = 类别数 |
| `bars_categorical_dual` | `labels[]` `series{}`（两个不同量纲，左右轴各一）| 两系列长度 = 类别数 |
| `median_iqr_by_vintage` | `labels[]` `median[]` `p25[]` `p75[]` `n[]` `overlay[]` | 四个数组等长；**P25 ≤ 中位 ≤ P75**；`n` 必须一起画出来 |
| `band_positioning` | `bands[]` `items[]` | — |
| `scatter_bubble` | `points[]` `label_managers[]` | — |
| `pct_history` | `history{fund:[{quarter,percentile,n}]}` `history_gaps{}` | 期次不重复且含本季；**只追加**；空历史必须在 `history_gaps` 里写明原因 |
| `rows_qoq` | `rows[{label,pq,cq,qoq,…}]` | 环比 = cq − pq |
| `rows_flat` | `rows[]`（dict 或矩阵行 list）| — |

> ⛔ **和形状无关的空字段要删掉。** 模板里带过来的 `lines: {}`、`vals: []` 之类留在
> 不该有它的形状上，会让审计脚本把「真缺口」和「模板残留」混在一起
> （2026Q3 收尾时清掉了 13 处这种残留）。判断标准见 `fix_pass.py` 里的 `KEEP` 表。

### 记住例外的字段

数值以外的东西也要入账，否则下季重跑会重新踩一遍：

| 字段 | 干什么 |
|---|---|
| `_method` | 这个数是怎么来的（明值 / 像素还原 / 计算），一句话 |
| `_caveat` | 读数限制（无锚点、点线采样误差、样本太薄）|
| `_source_axis_min` | 原图纵轴起点 —— 柱图重画要从 0 起，这里留证据 |
| `_gap_note` / `_hard_gap` | 为什么没有数；**不许拿旧报告的值顶上** |
| `_rounding_note` | 为什么加总不是 100%（原图各切片各自四舍五入）|
| `_basis_change` | 分母/口径跨季变了（例：Guggenheim 的 GICS 饼 4Q25 是 %NAV、1Q26 是 %Par）|
| `_moved_note` | 原来填错了、已挪到别处备用的数据 |
| `overlay` / `overlay_missing` | 自家基金叠加点，以及哪只没叠、为什么 |

## 顶层还有一个 `series_bank`

和 `meta` / `exhibits` 平级。存**已经找定、跨季只追加、但本季不一定有 exhibit 在画**的序列：

```json
"series_bank": {
  "<bank_slug>": {
    "_what":  "这是什么口径 —— ⚠ 第一句就写口径警告（回报 ≠ 收益率、YTW ≠ effective yield…）",
    "src":    "文件名 + slide 标题 + 左/右哪半边，规则同下面的《`src` 怎么写》",
    "periods": ["4Q14", "…", "1Q26"],
    "<series_name>": [ … ],
    "_method": "怎么量的 / 怎么取的（像素标定参数写全，下季能照着重做）",
    "_anchors": {"<锚点名>": {"measured": 8.73, "source_text": 8.7, "diff_pp": 0.03}},
    "_traps":   ["下季会再踩的坑，一条一句"],
    "source_latest_period": { … 同 exhibit 的写法，含 folder_freshest … },
    "_used_by": "本季哪张图在用；没有就写没有，以及为什么还要存"
  }
}
```

**为什么要有它**：Alex 2026-08-24 —— 「历史数据点记得都写进账本」「以后重要的点就可以放在
series 里，不用以后季度重新找了」。量一张 46 期的研报图要标定 + 锚点校验 + 排图例干扰，
一次半小时；不存下来，下季从零再来一遍，而且第二次量出来的数和第一次必然有零点几 pp 的差，
跨季对比就废了。

⚠ **`_what` 的口径警告是硬要求。** `series_bank` 里的序列没有 exhibit 的 Note 保护，
最容易被下一季误当成「同主题的更长历史」拿去补别的图。2026Q3 的实例：
`ms_p41L_yields`（收益率，4Q17 起）和 Ex 9 在画的回报序列（4Q14 起）同主题不同口径 ——
回报里有 −8.8% 和 +18.7%，收益率不可能有这种值，两边永远不许互填。口径警告写在第一个字段就是防这个。

## `src` 怎么写

**必须含文件名。** 而且:

> ⛔ **不许只靠 slide 号定位。** MS Tracker 的 slide 号每季一定挪 —— 框架里那批
> `slide 7 / 10 / 22 / 24 / 26 / 27 / 28 / 29` 下一季就不对了。
> 要写 **slide 的标题文字**，页码只做辅助。

```json
"src": "MS Private Credit 3Q26 tracker.pdf，slide 标题 \"Nonaccruals across BDCs\"（BDC Collateral）；页码约 7，仅供参考"
```

两级约定:
- **图级 `src`** —— 说清哪一期出自哪份文件的哪个位置
- **点级 `src`** —— 只记差异（口径例外、自算公式），其余写 `same`

`pc_review_sheet.py` 硬查三条:非空、含文件名、没有只靠 slide 号定位的。

## 三个基准日必须分别声明

| 层 | 基准 | 归属的节 |
|---|---|---|
| `market` | 本季或上季（看数据商）| §2–§7 |
| `fund` | **通常滞后 1–2 季** | §8 |
| `competitor` | PitchBook **导出日** | §9 |

`pc_review_sheet.py` 会检查三个都填了，且基金层不晚于市场层（晚了就是填错）。
基金层滞后时会提醒:**§8 开头必须显式声明这个滞后**，否则读者会把三个当同一时点。

## 纪律

1. **只追加，不重算。** 已冻结的历史点不许改。改了要写明理由和新的 `src`。
2. **`percentile_history` 只 append。** `ca_traj_*` 那两张轨迹图靠它重建。
3. **上一版报告不能当来源。** `src` 命中 `_v\d` / 报告名 直接 fail。
4. **缺数就报错，不许填占位。** 占位一旦落盘就没人回去核了。
5. **动态题注（15 个）** 的 `caption_rendered` 必填，且题注里每个数字都要能在账本里找到。

## 第一次怎么建

```bash
cp series_template.json series.json      # 骨架：58 个 slug 都在，数据字段空
# 填 meta.rq / meta.as_of / meta.screen / meta.comparator_set
# 然后一节一节取数，每填一个点就写 src
python3 pc_review_sheet.py               # 看恒等式和覆盖检查
```

第一次要填满 58 个 exhibit（实打实的活）。之后每季只追加本季那一期。
