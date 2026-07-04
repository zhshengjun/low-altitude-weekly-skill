# HTML 周报样例

本 skill 默认不再交付自由 Markdown 正文。样例输入见 `examples/sample-report.json`，其中：

- `analysis` 生成“分析专栏”
- `selected` 生成短讯式“优选信息”，并保留内部资讯评分 `scores`
- `tenders` 生成“本周招标信息”和全国/浙江热力图

生成预览：

```bash
python3 scripts/fill_template.py examples/sample-report.json --output /tmp/weekly-hotspot-sample.html
python3 scripts/build.py /tmp/weekly-hotspot-sample.html --report-json examples/sample-report.json
```

最终 PDF 由用户在浏览器打开 HTML 后打印/导出。
