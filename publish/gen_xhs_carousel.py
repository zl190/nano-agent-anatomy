"""Generate 小红书 carousel images (1440x2400, 3:5 ratio) for the experiment post."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent / "images" / "xhs-carousel"
OUT.mkdir(parents=True, exist_ok=True)

# ── Color palette ──
C_V1 = "#2563EB"      # blue (free text)
C_V2 = "#F59E0B"      # amber (structured JSON)
C_BG = "#0F172A"       # dark slate background
C_BG2 = "#1E293B"      # lighter slate for cards
C_TEXT = "#F8FAFC"      # near-white
C_ACCENT = "#10B981"    # green highlights
C_RED = "#EF4444"
C_DIM = "#94A3B8"       # dimmed text
C_PINK = "#F472B6"      # pink accent for CTA

# ── CJK font discovery (same as gen_images.py) ──
import matplotlib.font_manager as fm
_cjk_font = None
for _p in ["/System/Library/Fonts/Hiragino Sans GB.ttc",
           "/System/Library/Fonts/STHeiti Medium.ttc"]:
    try:
        _cjk_font = fm.FontProperties(fname=_p).get_name()
        fm.fontManager.addfont(_p)
        break
    except Exception:
        continue

plt.rcParams.update({
    "figure.facecolor": C_BG,
    "axes.facecolor": C_BG,
    "text.color": C_TEXT,
    "axes.labelcolor": C_TEXT,
    "xtick.color": C_TEXT,
    "ytick.color": C_TEXT,
    "font.family": [_cjk_font or "Hiragino Sans GB", "Helvetica Neue", "Arial"],
    "font.size": 14,
})

# XHS carousel: 1440x2400 at 200dpi -> 7.2 x 12 inches
W_IN, H_IN = 7.2, 12.0
DPI = 200


def new_page():
    """Create a new figure sized for XHS carousel."""
    fig, ax = plt.subplots(figsize=(W_IN, H_IN))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 16.67)  # proportional to 3:5 aspect
    ax.axis('off')
    return fig, ax


def box(ax, x, y, w, h, text, color, fontsize=14, text_color=C_TEXT):
    """Draw a rounded box with centered text."""
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                                    facecolor=color, edgecolor=C_TEXT, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fontsize, color=text_color, fontweight='bold', wrap=True)


def arrow(ax, x1, y1, x2, y2, color=C_TEXT):
    """Draw an arrow between two points."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=2.5))


def save_page(fig, name):
    """Save figure at exact 1440x2400 pixels."""
    fig.savefig(OUT / name, dpi=DPI, facecolor=C_BG)
    plt.close(fig)


# ════════════════════════════════════════════════════════════
# Page 1: Cover / Hook
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

# Decorative top accent line
ax.plot([1, 9], [15.5, 15.5], color=C_ACCENT, linewidth=4, alpha=0.6)
ax.plot([1, 9], [15.3, 15.3], color=C_V1, linewidth=2, alpha=0.4)

# Main hook text
ax.text(5, 12.5, "我读了51万行", fontsize=52, ha='center', va='center',
        fontweight='bold', color=C_TEXT)
ax.text(5, 10.8, "公开源码", fontsize=52, ha='center', va='center',
        fontweight='bold', color=C_ACCENT)

# Divider
ax.plot([3, 7], [9.5, 9.5], color=C_DIM, linewidth=1.5, alpha=0.5)

ax.text(5, 8.0, "发现了什么?", fontsize=48, ha='center', va='center',
        fontweight='bold', color=C_V2)

# Subtitle
ax.text(5, 5.8, "6个AI盲评 · 结构化 vs 自由文本", fontsize=22, ha='center',
        va='center', color=C_DIM)

# Bottom tag
props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_ACCENT, alpha=0.9)
ax.text(5, 3.5, "Claude Code · 实验实录", fontsize=20, ha='center',
        va='center', bbox=props, color=C_ACCENT)

# Page indicator
ax.text(5, 1.2, "1 / 8  →  左滑看结果", fontsize=16, ha='center',
        va='center', color=C_DIM, alpha=0.7)

save_page(fig, "01-cover.png")


# ════════════════════════════════════════════════════════════
# Page 2: Experiment Setup
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

ax.text(5, 15.2, "实验设计", fontsize=36, ha='center', fontweight='bold', color=C_ACCENT)

ax.text(5, 14.0, "盲测: 自由文本 vs 结构化JSON", fontsize=28, ha='center',
        fontweight='bold', color=C_TEXT)

# Step boxes
steps = [
    ("01", "读源码", "Claude Code 51万行公开源码\n6个 Sonnet agent 分头读核心模块", C_V1),
    ("02", "两轮跑", "第一轮: 自由 Markdown (无限制)\n第二轮: 结构化 JSON (schema约束)", C_V2),
    ("03", "盲评", "输出匿名后\n独立 Opus 评审员打分\n不知道哪个是 v1 / v2", C_ACCENT),
]

y = 11.8
for num, title, desc, color in steps:
    # Number circle
    circle = mpatches.Circle((1.5, y - 0.3), 0.55, facecolor=color, edgecolor='none')
    ax.add_patch(circle)
    ax.text(1.5, y - 0.3, num, fontsize=22, ha='center', va='center',
            fontweight='bold', color=C_BG)
    # Title
    ax.text(3.0, y, title, fontsize=24, ha='left', va='center',
            fontweight='bold', color=color)
    # Description
    ax.text(3.0, y - 1.2, desc, fontsize=17, ha='left', va='center',
            color=C_DIM, linespacing=1.6)
    # Connecting line
    if num != "03":
        ax.plot([1.5, 1.5], [y - 0.85, y - 2.8], color=C_DIM, linewidth=1.5, alpha=0.4)
    y -= 3.6

# Question at bottom
props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_V2, alpha=0.9)
ax.text(5, 1.8, "猜猜哪个赢了?", fontsize=26, ha='center', va='center',
        bbox=props, color=C_V2, fontweight='bold')

save_page(fig, "02-experiment-setup.png")


# ════════════════════════════════════════════════════════════
# Page 3: Score Comparison Chart
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(W_IN, H_IN))

dims = ["提取完整度\nExtraction", "模式深度\nPattern Depth", "证据质量\nEvidence",
        "交叉引用\nCross-Ref", "实用性\nActionability"]
v1 = [4.50, 5.00, 3.33, 4.33, 5.00]
v2 = [4.83, 4.00, 4.67, 4.33, 3.83]

x = np.arange(len(dims))
w = 0.35

bars1 = ax.barh(x + w/2, v1, w, color=C_V1, label="v1 自由文本", zorder=3)
bars2 = ax.barh(x - w/2, v2, w, color=C_V2, label="v2 结构化JSON", zorder=3)

# Value labels
for bar, val in zip(bars1, v1):
    color = C_ACCENT if val >= 5.0 else C_TEXT
    ax.text(val + 0.08, bar.get_y() + bar.get_height()/2, f"{val:.2f}",
            va='center', ha='left', fontsize=18, fontweight='bold', color=color)

for bar, val in zip(bars2, v2):
    color = C_ACCENT if val >= 4.67 else C_TEXT
    ax.text(val + 0.08, bar.get_y() + bar.get_height()/2, f"{val:.2f}",
            va='center', ha='left', fontsize=18, fontweight='bold', color=color)

# Winner markers
for i, (a, b) in enumerate(zip(v1, v2)):
    if a > b:
        ax.annotate("v1 WIN", xy=(max(a, b) + 0.55, i + w/2), fontsize=14,
                     color=C_V1, fontweight='bold', va='center')
    elif b > a:
        ax.annotate("v2 WIN", xy=(max(a, b) + 0.55, i - w/2), fontsize=14,
                     color=C_V2, fontweight='bold', va='center')
    else:
        ax.annotate("Tie", xy=(max(a, b) + 0.55, i), fontsize=14,
                     color=C_DIM, va='center')

ax.set_yticks(x)
ax.set_yticklabels(dims, fontsize=17)
ax.set_xlim(0, 6.5)
ax.set_xlabel("")
ax.legend(loc="lower right", fontsize=16, framealpha=0.3)
ax.set_title("6个AI盲评 · 5维度对比", fontsize=28, fontweight='bold', pad=25)
ax.grid(axis='x', alpha=0.15, zorder=0)
ax.invert_yaxis()

# Summary box
summary = "总分: v1 preferred 6:1\n自由文本完胜"
props = dict(boxstyle='round,pad=0.8', facecolor=C_BG2, edgecolor=C_ACCENT, alpha=0.9)
ax.text(3.3, 4.8, summary, fontsize=18, va='center', ha='center',
        bbox=props, color=C_ACCENT, fontweight='bold')

plt.tight_layout()
fig.savefig(OUT / "03-score-comparison.png", dpi=DPI, facecolor=C_BG)
plt.close()


# ════════════════════════════════════════════════════════════
# Page 4: Key Finding - Big Number
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

ax.text(5, 14.5, "结果揭晓", fontsize=28, ha='center', va='center',
        color=C_DIM, fontweight='bold')

# Big ratio
ax.text(5, 11.5, "6 : 1", fontsize=120, ha='center', va='center',
        fontweight='bold', color=C_ACCENT)

ax.text(5, 9.5, "自由文本完胜", fontsize=42, ha='center', va='center',
        fontweight='bold', color=C_V1)

# Divider
ax.plot([2, 8], [8.3, 8.3], color=C_DIM, linewidth=1.5, alpha=0.5)

# Detail cards
details = [
    ("结构化只赢了", "证据质量 (+1.33)", C_V2),
    ("但输了", "洞察深度 (-1.00)", C_V1),
    ("还输了", "实用性 (-1.17)", C_V1),
]

y = 7.2
for label, value, color in details:
    ax.text(2.5, y, label, fontsize=20, ha='left', va='center', color=C_DIM)
    ax.text(5.5, y, value, fontsize=22, ha='left', va='center',
            fontweight='bold', color=color)
    y -= 1.3

# Killer quote
props = dict(boxstyle='round,pad=0.8', facecolor=C_BG2, edgecolor=C_RED, alpha=0.9)
ax.text(5, 2.5, "JSON 把 agent 变成了索引机器\n能检索, 但说不出\n\"这个代码库本质上是个XX\"",
        fontsize=20, ha='center', va='center', bbox=props, color=C_RED,
        linespacing=1.8, fontweight='bold')

save_page(fig, "04-key-finding.png")


# ════════════════════════════════════════════════════════════
# Page 5: v3 Dual-Channel Diagram
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

# Title
ax.text(5, 15.5, "v3 方案", fontsize=36, ha='center', fontweight='bold', color=C_ACCENT)
ax.text(5, 14.5, "结构提取 + 自由解读 = 两全其美", fontsize=22, ha='center', color=C_DIM)

# Source code box
box(ax, 2.5, 12.5, 5, 1.2, "Source Code\n51万行公开源码", "#334155", 18)

# Split arrows
arrow(ax, 3.5, 12.5, 2.5, 11.5)
arrow(ax, 6.5, 12.5, 7.5, 11.5)

# Left channel: JSON extraction
box(ax, 0.3, 9.8, 4.2, 1.5, "JSON 提取\nHaiku (便宜)", C_V2, 18)
ax.text(2.4, 9.2, "symbols / signatures\nfile:line evidence", ha='center',
        fontsize=14, color=C_DIM, style='italic')

# Right channel: Markdown interpretation
box(ax, 5.5, 9.8, 4.2, 1.5, "自由解读\nSonnet / Opus", C_V1, 18)
ax.text(7.6, 9.2, "pattern depth / insights\n\"教程不会教你的\"", ha='center',
        fontsize=14, color=C_DIM, style='italic')

# Arrows down
arrow(ax, 2.4, 9.8, 2.4, 8.7)
arrow(ax, 7.6, 9.8, 7.6, 8.7)

# Gate boxes
box(ax, 0.3, 7.2, 4.2, 1.3, "Schema Gate\nJSON 必须 parse", "#065F46", 16)
box(ax, 5.5, 7.2, 4.2, 1.3, "No Gate\n不限制叙述自由", "#7C2D12", 16)

# Arrows to merge
arrow(ax, 2.4, 7.2, 4.2, 6.0)
arrow(ax, 7.6, 7.2, 5.8, 6.0)

# Merged output
box(ax, 1.5, 4.5, 7, 1.5, "双通道输出\n结构化数据 + 深度洞察", C_ACCENT, 20)

# Cost note
ax.text(5, 3.5, "成本 ~$4.50", fontsize=18, ha='center', color=C_DIM)
ax.text(5, 2.8, "Haiku 提取 $1.50 + Sonnet 解读 $3.00",
        fontsize=15, ha='center', color=C_DIM)

# Score preservation
scores = "v1 洞察深度 5.0 \u2190 保留\nv2 证据质量 4.67 \u2190 保留\n= 两个优势合并"
props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_ACCENT, alpha=0.9)
ax.text(5, 1.3, scores, fontsize=17, ha='center', va='center',
        bbox=props, color=C_ACCENT, linespacing=1.8, fontweight='bold')

save_page(fig, "05-v3-dual-channel.png")


# ════════════════════════════════════════════════════════════
# Page 6: Blind Evaluator Quotes
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

ax.text(5, 15.2, "盲评原文", fontsize=36, ha='center', fontweight='bold', color=C_ACCENT)
ax.text(5, 14.2, "Opus 评审员 \u00b7 不知道哪个是 v1/v2", fontsize=18,
        ha='center', color=C_DIM)

quotes = [
    ('\u201cA reads like someone who\nunderstood the code,\nnot someone who indexed it.\u201d',
     "\u2014 评价 v1 自由文本", C_V1),
    ('\u201cB would be better for building\nautomated tooling on top of\nthe reading.\u201d',
     "\u2014 评价 v2 结构化", C_V2),
    ('\u201cThe pattern density map and\n10 surprising findings demonstrate\nthe kind of output that justifies\nspending time reading source code.\u201d',
     "\u2014 评价 v1 综合能力", C_ACCENT),
]

y = 12.8
for quote, attrib, color in quotes:
    # Quote background
    rect = mpatches.FancyBboxPatch((0.8, y - 3.0), 8.4, 3.5,
                                    boxstyle="round,pad=0.4",
                                    facecolor=C_BG2, edgecolor=color, linewidth=2.5)
    ax.add_patch(rect)
    # Left accent bar
    rect2 = mpatches.FancyBboxPatch((0.8, y - 3.0), 0.18, 3.5,
                                     boxstyle="square,pad=0",
                                     facecolor=color, edgecolor='none')
    ax.add_patch(rect2)
    ax.text(5, y - 0.9, quote, fontsize=18, ha='center', va='center',
            color=C_TEXT, style='italic', linespacing=1.6)
    ax.text(8.7, y - 2.7, attrib, fontsize=14, ha='right', va='center',
            color=color, fontweight='bold')
    y -= 4.2

save_page(fig, "06-blind-eval-quotes.png")


# ════════════════════════════════════════════════════════════
# Page 7: Takeaway
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

ax.text(5, 14.5, "核心结论", fontsize=32, ha='center', va='center',
        color=C_DIM, fontweight='bold')

# Main takeaway
ax.text(5, 11.8, "结构帮验证", fontsize=48, ha='center', va='center',
        fontweight='bold', color=C_V2)
ax.text(5, 10.2, "自由帮洞察", fontsize=48, ha='center', va='center',
        fontweight='bold', color=C_V1)

# Divider
ax.plot([2.5, 7.5], [8.8, 8.8], color=C_ACCENT, linewidth=3, alpha=0.6)

ax.text(5, 7.5, "别用同一个格式", fontsize=36, ha='center', va='center',
        fontweight='bold', color=C_ACCENT)

# Two column comparison
# Left: structured strengths
left_props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_V2, alpha=0.9)
ax.text(2.8, 5.2, "结构化 JSON\n> 证据标注\n> 自动解析\n> Schema 验证",
        fontsize=18, ha='center', va='center', bbox=left_props,
        color=C_V2, linespacing=1.8, fontweight='bold')

# Right: free text strengths
right_props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_V1, alpha=0.9)
ax.text(7.2, 5.2, "自由文本\n> 模式发现\n> 深度洞察\n> 叙事表达",
        fontsize=18, ha='center', va='center', bbox=right_props,
        color=C_V1, linespacing=1.8, fontweight='bold')

# Arrow pointing to merge
ax.text(5, 3.0, "+", fontsize=40, ha='center', va='center', color=C_ACCENT)

# v3 conclusion
v3_props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_ACCENT, alpha=0.9)
ax.text(5, 1.5, "v3: 分开跑, 分开把关, 两全其美",
        fontsize=20, ha='center', va='center', bbox=v3_props,
        color=C_ACCENT, fontweight='bold')

save_page(fig, "07-takeaway.png")


# ════════════════════════════════════════════════════════════
# Page 8: CTA
# ════════════════════════════════════════════════════════════
fig, ax = new_page()

# Top decoration
ax.plot([1, 9], [15.0, 15.0], color=C_ACCENT, linewidth=4, alpha=0.6)

ax.text(5, 13.0, "完整实验数据", fontsize=40, ha='center', va='center',
        fontweight='bold', color=C_TEXT)

ax.text(5, 11.5, "+", fontsize=36, ha='center', va='center', color=C_DIM)

ax.text(5, 10.0, "代码已开源", fontsize=40, ha='center', va='center',
        fontweight='bold', color=C_ACCENT)

# Arrow
ax.text(5, 8.2, "\u2193", fontsize=60, ha='center', va='center', color=C_PINK)

# CTA box
cta_props = dict(boxstyle='round,pad=1.0', facecolor=C_PINK, edgecolor='none', alpha=0.9)
ax.text(5, 6.0, "评论区见链接", fontsize=36, ha='center', va='center',
        bbox=cta_props, color=C_BG, fontweight='bold')

# Engagement prompt
ax.text(5, 3.5, "你平时让 AI 读代码\n用自由提问还是给模板?", fontsize=24,
        ha='center', va='center', color=C_DIM, linespacing=1.8)

# Interaction prompt
interact_props = dict(boxstyle='round,pad=0.6', facecolor=C_BG2, edgecolor=C_DIM, alpha=0.7)
ax.text(5, 1.5, "评论聊聊 | 收藏备用", fontsize=20, ha='center',
        va='center', bbox=interact_props, color=C_DIM)

save_page(fig, "08-cta.png")


# ── Summary ──
print(f"Generated 8 carousel images in {OUT}/")
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name}")
