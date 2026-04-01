# 小红书 第0期

## 标题
6个AI盲评，结构化读源码惨败

## 正文

JSON schema + 验证门禁 + 架构 persona，精心设计的结构化流程，被零流程的 baseline 打爆了。

Claude Code 51万行泄露源码，我让6个 Sonnet agent 分头读（QueryEngine.ts、BashTool/ 等），跑两轮：一轮自由 Markdown，一轮结构化 JSON。匿名后独立 Opus 盲评。

结果：自由文本 6:1 完胜。

结构化赢了"证据质量"（+1.33），但输了"洞察深度"（-1.00）和"可操作性"（-1.17）。JSON 把 agent 变成了索引员——产出能 grep，但没有"这个代码库其实是个游戏引擎"这种改变认知的洞察。

结论：**结构帮验证，自由帮洞察。不该用同一个格式。**

v3 方案：先 JSON 提取（Haiku，便宜），再自由文本解读（Sonnet/Opus）。分开跑，分开 gate。

完整实验报告：experiment-report.md（含评分表 + 评语原文）

实验数据 + 代码开源 👇
📎 github.com/zl190/nano-agent-anatomy

## Tags
#AI #Claude #Agent #LLM #AI实验 #程序员必看 #源码分析 #编程

## 图片描述
截图1: 5维度得分对比表（高亮 Pattern Depth 5.00 vs 4.00，Evidence 3.33 vs 4.67）
截图2: v3 dual-channel 流程图（左 JSON extraction → 右 Markdown interpretation）
截图3: blind eval 评语截图："reads like someone who understood the code, not someone who indexed it"
