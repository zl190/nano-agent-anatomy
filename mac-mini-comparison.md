---
title: "Mac Mini M4 选购对比"
author: ""
date: 2026-04
header-includes: |
  \usepackage{luatexja-fontspec}
  \setmainjfont{Noto Sans CJK SC}
  \setsansjfont{Noto Sans CJK SC}
  \usepackage{booktabs}
  \usepackage{colortbl}
  \definecolor{pick}{RGB}{39,174,96}
---

# 需求分析

## 用途定位

- **Always-on CC hub** — MacBook / iPhone 远程接入
- **Chrome MCP** — 无头浏览器自动化
- **本地模型推理** — 14B\textasciitilde{}32B 参数量化模型
- **不需要做的事** — 重训练 / 大数据（另有 GPU 服务器）

## 关键约束

- Apple Silicon **统一内存 = 显存**，内存决定能跑多大模型
- 硬盘可外接 TB4 SSD，内存只能买时选
- \textcolor{pick}{朋友学校可报销} → 预算可放宽

# 配置对比

## 四档配置一览

\begin{table}
\centering
\begin{tabular}{@{}lcccl@{}}
\toprule
& \textbf{16GB} & \textbf{24GB} & \textbf{32GB} & \textbf{64GB} \\
\midrule
价格 (US) & \$499 & \$599 & \$799 & \$1,399 \\
CC hub & \checkmark & \checkmark & \checkmark & \checkmark \\
7\textasciitilde{}8B 量化 & 勉强 & 流畅 & 流畅 & 流畅 \\
14B Q4 & $\times$ & \checkmark & \checkmark & \checkmark \\
32B Q4 & $\times$ & $\times$ & \checkmark & \checkmark \\
70B Q4 & $\times$ & $\times$ & $\times$ & \checkmark \\
\bottomrule
\end{tabular}
\end{table}

\vspace{0.3em}
\small 70B 可用独立 GPU 服务器跑，Mac Mini 不需要覆盖

# 存储方案

## 内置 vs 外接

\begin{table}
\centering
\begin{tabular}{@{}lcc@{}}
\toprule
& \textbf{Apple 内置升级} & \textbf{外接 TB4 SSD} \\
\midrule
512GB 价格 & +\$200 & --- \\
1TB 价格 & +\$400 & \textasciitilde\$100 \\
读写速度 & \textasciitilde{}7 GB/s & \textasciitilde{}3 GB/s \\
模型加载影响 & 快几秒 & 加载后常驻内存，无差别 \\
灵活性 & 固定 & 可换机器 \\
\bottomrule
\end{tabular}
\end{table}

\vspace{0.5em}
\centering \textbf{结论：内存别省，硬盘外挂}

# 推荐方案

## 两档推荐

\begin{table}
\centering
\begin{tabular}{@{}lll@{}}
\toprule
& \textbf{实用档} & \textbf{宽裕档} \\
\midrule
配置 & 24GB / 256GB 内置 & 32GB / 256GB 内置 \\
外接 & 1TB TB4 SSD & 1TB TB4 SSD \\
Mac Mini 价格 & \$599 & \$799 \\
外接 SSD & \textasciitilde\$100 & \textasciitilde\$100 \\
\textbf{总计} & \textbf{\textasciitilde\$700} & \textbf{\textasciitilde\$900} \\
\midrule
能跑 & 14B Q4 流畅 & 32B Q4 流畅 \\
适合 & 当前够用 & 多一年模型寿命 \\
\bottomrule
\end{tabular}
\end{table}

## 决策树

1. 只当 CC hub，不跑模型 → 16GB \$499（但报销的话没必要省）
2. 跑 14B 本地模型 → \textcolor{pick}{24GB \$599 + 外接 SSD ≈ \$700}
3. 报销额度宽裕 → \textcolor{pick}{32GB \$799 + 外接 SSD ≈ \$900}
4. 70B 本地 → 不建议，用独立 GPU 服务器
