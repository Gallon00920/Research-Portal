# 输入：文件夹与文件识别规则

### 1. 输入：文件夹与文件识别规则


运行时提供的路径形如：

```
...\04 Research\Software\<YYYY>Q<n> - Software\Report
```

实际结构（以 2026Q2 为例）：

```
Report\
├─ 202607OTF 草稿 - 副本.xlsx                          内部模型
├─ OTF_2026Q2_Fundamental_Analysis_Report.docx          （不作为生图数据源）
├─ OTF\
│   ├─ OTF Q2.pdf                                       当季 10-Q（26.9MB）
│   ├─ Q2'26 OTF Earnings Presentation_vF.pdf           当季 earnings deck
│   ├─ 2 - OTF 10-Q季报 2026Q1.pdf                      上季 10-Q
│   ├─ 3 - Q1'26 OTF Earnings Presentation (05.06.26).pdf  上季 deck
│   ├─ 2.1 - OTF 10-Q 3Q25季报.pdf
│   ├─ OTF报告 - Baml.pdf                               当季 BofA
│   ├─ Challenging quarter; yield pressure, NAV.pdf      上季 BofA
│   ├─ Barclays_BDC_Comp_Table.pdf
│   └─ 历史报告\
│        0001747777-25-000008.pdf   0001747777-25-000015.pdf
│        0001747777-25-000024.pdf   0001747777-25-000048.pdf
│        0001747777-26-000012.pdf   0001747777-26-000019.pdf
├─ competitor earnings\
│   arcc2026q2.pdf  bxsl2026q2.pdf  gbdc2026Q2.pdf  obdc2026Q2.pdf  tslx2026Q2.pdf
└─ 行业\
    ├─ 1 - Broker public BDCs sentiment\
    │    Private Credit Tracker 1Q26 – Softening Fundamentals.pdf
    │    JPM_BDCs__PIKing_into_PI_2026-06-15_5332893.pdf
    │    JPM_BDC_Flows_2Q_26_Rede_2026-07-09_5358607.pdf
    │    JPM_BDC_Quarterly_Earnin_2026-04-06 / 2026-05-20 ...
    │    Global Credit Trader_ Software Exposure in Leveraged Credit....pdf
    │    Connecting the Dots Around Private Credit.pdf 等
    ├─ 1 - Broker Software+AI\        UBS / GS / BofA 的 AI×软件研报
    ├─ 2 - private credit news\  2 - Website - News\  3 - Earningcall Transcript\
    └─ OTF & BlueOwl NEWS .docx
```

### 1.1 生图只用这三个来源

| 来源 | 供给哪些图 |
|---|---|
| `OTF\`（含 `历史报告\`） | 图 1–7（组合、收益率、NAV bridge、NII、PIK、非应计、内部评级） |
| `competitor earnings\` + `OTF\` 当季 10-Q | 图 10–14（BDC 竞品五指标对比） |
| `行业\1 - Broker public BDCs sentiment\` | 图 15–20（行业杠杆/覆盖/非应计/PIK/分行业） |
| `行业\1 - Broker Software+AI\` | 图 21（软件分层示意图，**层数每季按研报重定**）|
| 联网行情 | 图 8–9（股价走势）；文件夹内没有价格文件 |
| `<YYYYMM>OTF 草稿*.xlsx` | 仅供**图 1 的文字点评**引用 AI-impact 分级；不作为图内数据 |

### 1.2 文件识别规则（**不要依赖文件名**）

- **当季 10-Q**：把 `OTF\` 下所有 PDF 打开首页，读 `For the quarterly period ended <date>`，取日期最新的那份。（Q1 报告期用上一年 **10-K**，锚点为 `For the fiscal year ended <date>`。）
- **当季 earnings deck**：`OTF\` 下文件名含 `Earnings Presentation` 且封面季度 = CQ 的那份。
- **历史序列**：`历史报告\` 下 6 份按 SEC accession 号命名的 PDF，**逐份打开读封面期末日**建立 `accession → 期末日` 映射，再按需取用。以 2026Q2 为例映射为：`25-000015→Q1'25`、`25-000024→Q2'25`、`25-000048→Q3'25`、`26-000012→FY25(10-K)`、`26-000019→Q1'26`；`25-000008` 为更早一期。**每季重新建映射，绝不套用上一季的结论。**
- **竞品 filings**：`competitor earnings\` 下文件名前缀即 ticker（arcc/bxsl/gbdc/obdc/tslx），大小写不敏感；季度后缀不区分大小写（`2026q2` / `2026Q2` 都要能匹配）。
- **MS Private Credit Tracker**：`行业\1 - Broker public BDCs sentiment\` 下文件名含 `Private Credit Tracker` 的那份，季度取文件名里的 `<n>Q<yy>`。
- **JPM PIK 报告**：文件名含 `PIKing_into_PI` 的那份。
- **缺件处理**：某个来源缺失 → 跳过靠它的图、表和小节，**报告里整块删掉、不写缺件说明**，图号顺延，规则见 `SKILL.md`「缺料」一节。**不许用旧季文件冒充当季。**

---
