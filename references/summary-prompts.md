# 总结提示词

用于把已核验资讯整理为《本周热点分析》的 `report.json`。输出中文，稳健正式，避免空话。

## 分析专栏

```text
请基于以下已核验资讯，写一篇中文分析专栏。

要求：
1. 标题为编辑生成的判断型标题，4 到 40 个汉字左右，不照抄原文标题。
2. 元数据保留 source_name、source_url、published_at。
3. summary 用 2 到 4 句话概括事实变化、重要性和影响。
4. paragraphs 写 3 到 5 个自然段，合计不少于 500 字。
5. 正文必须覆盖事实触发、趋势判断、影响链条、约束条件和后续关注变量。
6. 不写“总体判断”“最终分析结论”“AI分析：”。
7. 不写“这条信息/该资讯/价值在于”等播报腔。

领域：{领域}
统计周期：{开始日期} 至 {结束日期}
资讯：{items}
```

## 优选信息

优选信息参考低空周报短讯形态，一条信息只写 2 到 3 句话。

生成前先按 `references/scoring-rubric.md` 对候选资讯逐条评分。评分只用于筛选排序，默认不在 HTML 正文展示。

```text
请基于以下已核验资讯，生成优选信息短讯。

要求：
1. 每条标题格式为“动态类型：主体或地区 + 核心动作”，例如“政策动态：浙江上线低空飞行服务模块”。
2. 每条保留 source_name、source_url、published_at。
3. paragraphs 只放 2 到 3 句话，直接说明主体、动作、时间、地点和意义。
4. 不写长篇评论，不写段落式深度分析，不写“该信息说明”。
5. 每条 selected 保留 scores 字段，字段和公式按 references/scoring-rubric.md 执行。
6. 先按动态类型分类，再按 composite 综合得分降序排列；得分相同时，发布时间更近者排前。
7. 优先保留 8 到 15 条；资料稀少时可少于 8 条，但必须说明已完成补搜。

领域：{领域}
统计周期：{开始日期} 至 {结束日期}
资讯：{items}
```

## 招标信息

```text
请基于用户上传或已核验的招标表格，整理 tenders 数组。

字段：
- project_name：项目名称
- purchaser：采购主体
- region：省级地区
- city：地级市；浙江热力图必须尽量补齐
- budget：预算金额原文
- node：本周节点，如“投标期内”“文件获取期内”“7月3日投标截止”
- url：原文链接

只保留与主题相关、统计周期内、链接可访问或可追溯的项目。中标结果类公告默认不计入招标列表，除非用户明确要求。
```

## report.json 组装

```text
请把最终内容组装为 report.json，而不是自由 Markdown。

必须包含：
- meta.domain、meta.start_date、meta.end_date、meta.item_count、meta.category_count
- highlights：3 到 5 条
- analysis：1 到 2 条
- selected：8 到 15 条，资料稀少时可少于 8 条，但必须说明已完成补搜
- selected[].scores：两层六指标评分，仅用于筛选排序，不在 HTML 正文展示
- tenders：有上传招标表或任务要求招标时必须包含

填好后运行：
python3 scripts/fill_template.py report.json --output report.html
python3 scripts/build.py report.html --report-json report.json
```

## 自检修正

```text
请检查 report.json 和生成后的 HTML，只修正问题部分：
1. 是否有标题、统计周期、本周要点、目录、分析专栏、优选信息。
2. 优选信息是否为 2 到 3 句话短讯，不能是 250 字长文。
3. 优选信息是否都有 scores，且综合分与公式一致。
4. 分析专栏是否有摘要和 3 到 5 段深度正文。
5. 每条资讯是否有来源、发布时间、来源链接。
6. 有招标数据时，是否有招标表和全国/浙江热力图。
7. HTML 是否无 `{{...}}` 残留占位符。
8. 是否自动生成了 PDF；如有，删除默认 PDF 步骤，仅保留 HTML。
```
