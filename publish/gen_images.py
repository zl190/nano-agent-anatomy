"""Generate 小红书 post images from experiment data."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent / "images"
OUT.mkdir(exist_ok=True)

# Color palette
C_V1 = "#2563EB"   # blue
C_V2 = "#F59E0B"   # amber
C_BG = "#0F172A"   # dark slate
C_TEXT = "#F8FAFC"  # near-white
C_ACCENT = "#10B981"  # green for highlights
C_RED = "#EF4444"

import matplotlib.font_manager as fm
# Register CJK font
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

# ── Image 1: 5-dimension comparison bar chart ──
fig, ax = plt.subplots(figsize=(9, 12))

dims = ["Extraction\n提取完整度", "Pattern Depth\n模式深度", "Evidence\n证据质量",
        "Cross-Ref\n交叉引用", "Actionability\n可操作性"]
v1 = [4.50, 5.00, 3.33, 4.33, 5.00]
v2 = [4.83, 4.00, 4.67, 4.33, 3.83]

x = np.arange(len(dims))
w = 0.35

bars1 = ax.barh(x + w/2, v1, w, color=C_V1, label="v1 自由文本", zorder=3)
bars2 = ax.barh(x - w/2, v2, w, color=C_V2, label="v2 结构化JSON", zorder=3)

# Add value labels
for bar, val in zip(bars1, v1):
    color = C_ACCENT if val >= 5.0 else C_TEXT
    ax.text(val + 0.08, bar.get_y() + bar.get_height()/2, f"{val:.2f}",
            va='center', ha='left', fontsize=16, fontweight='bold', color=color)

for bar, val in zip(bars2, v2):
    color = C_ACCENT if val >= 4.67 else C_TEXT
    ax.text(val + 0.08, bar.get_y() + bar.get_height()/2, f"{val:.2f}",
            va='center', ha='left', fontsize=16, fontweight='bold', color=color)

# Highlight winners with arrows
for i, (a, b) in enumerate(zip(v1, v2)):
    if a > b:
        ax.annotate("v1 ✓", xy=(max(a, b) + 0.5, i + w/2), fontsize=13,
                     color=C_V1, fontweight='bold', va='center')
    elif b > a:
        ax.annotate("v2 ✓", xy=(max(a, b) + 0.5, i - w/2), fontsize=13,
                     color=C_V2, fontweight='bold', va='center')
    else:
        ax.annotate("Tie", xy=(max(a, b) + 0.5, i), fontsize=13,
                     color="#94A3B8", va='center')

ax.set_yticks(x)
ax.set_yticklabels(dims, fontsize=15)
ax.set_xlim(0, 6.2)
ax.set_xlabel("")
ax.legend(loc="lower right", fontsize=14, framealpha=0.3)
ax.set_title("6个AI盲评 · 5维度对比\nv1 自由文本 vs v2 结构化JSON", fontsize=20, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.15, zorder=0)
ax.invert_yaxis()

# Add summary box
summary = "总分: v1 preferred 6:1\n结构帮验证, 自由帮洞察"
props = dict(boxstyle='round,pad=0.8', facecolor='#1E293B', edgecolor=C_ACCENT, alpha=0.9)
ax.text(3.1, 4.8, summary, fontsize=15, va='center', ha='center', bbox=props, color=C_ACCENT)

plt.tight_layout()
fig.savefig(OUT / "01-score-comparison.png", dpi=200, bbox_inches='tight')
plt.close()

# ── Image 2: v3 dual-channel flow diagram ──
fig, ax = plt.subplots(figsize=(9, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

def box(ax, x, y, w, h, text, color, fontsize=14):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                                    facecolor=color, edgecolor=C_TEXT, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fontsize, color=C_TEXT, fontweight='bold', wrap=True)

def arrow(ax, x1, y1, x2, y2, color=C_TEXT):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=2))

# Title
ax.text(5, 13.3, "v3 Dual-Channel SOP", fontsize=22, ha='center', fontweight='bold', color=C_TEXT)
ax.text(5, 12.7, "结构提取 + 自由解读 = 两全其美", fontsize=15, ha='center', color="#94A3B8")

# Source code box
box(ax, 2.5, 11, 5, 1, "📁 Source Code\n513K lines", "#334155", 15)

# Split arrow
arrow(ax, 3.5, 11, 2.5, 10.2)
arrow(ax, 6.5, 11, 7.5, 10.2)

# Left channel: JSON extraction
box(ax, 0.5, 8.8, 4, 1.2, "🔧 JSON 提取\nHaiku (便宜)", C_V2, 14)
ax.text(2.5, 8.3, "symbols · signatures\nfile:line evidence", ha='center',
        fontsize=11, color="#94A3B8", style='italic')

# Right channel: Markdown interpretation
box(ax, 5.5, 8.8, 4, 1.2, "💡 自由解读\nSonnet/Opus", C_V1, 14)
ax.text(7.5, 8.3, "pattern depth · insights\n\"what tutorials don't teach\"", ha='center',
        fontsize=11, color="#94A3B8", style='italic')

# Arrows down
arrow(ax, 2.5, 8.8, 2.5, 7.5)
arrow(ax, 7.5, 8.8, 7.5, 7.5)

# Gate boxes
box(ax, 0.5, 6.2, 4, 1.2, "✅ Schema Gate\nJSON 必须 parse", "#065F46", 13)
box(ax, 5.5, 6.2, 4, 1.2, "🚫 No Gate\n不限制叙述自由", "#7C2D12", 13)

# Arrows to merge
arrow(ax, 2.5, 6.2, 4, 5.2)
arrow(ax, 7.5, 6.2, 6, 5.2)

# Merged output
box(ax, 2, 3.8, 6, 1.2, "📊 双通道输出\n结构化数据 + 深度洞察", C_ACCENT, 15)

# Cost note
ax.text(5, 3.0, "成本 ≈ $4.50 (Haiku提取$1.50 + Sonnet解读$3.00)",
        ha='center', fontsize=12, color="#94A3B8")

# Score comparison
scores = "v1 洞察深度 5.0 ← 保留\nv2 证据质量 4.67 ← 保留\n= 两个优势合并"
props2 = dict(boxstyle='round,pad=0.6', facecolor='#1E293B', edgecolor=C_ACCENT, alpha=0.9)
ax.text(5, 1.6, scores, fontsize=14, ha='center', va='center',
        bbox=props2, color=C_ACCENT, linespacing=1.8)

plt.tight_layout()
fig.savefig(OUT / "02-v3-dual-channel.png", dpi=200, bbox_inches='tight')
plt.close()

# ── Image 3: Blind eval quote card ──
fig, ax = plt.subplots(figsize=(9, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

ax.text(5, 12.5, "🔒 盲评原文", fontsize=24, ha='center', fontweight='bold', color=C_TEXT)
ax.text(5, 11.8, "Opus 评审员 · 不知道哪个是 v1/v2", fontsize=14, ha='center', color="#94A3B8")

quotes = [
    ('\u201cA reads like someone who\nunderstood the code,\nnot someone who indexed it.\u201d',
     "-- v1 free text", C_V1),
    ('\u201cB would be better for building\nautomated tooling on top of\nthe reading.\u201d',
     "-- v2 structured", C_V2),
    ('\u201cThe pattern density map and\n10 surprising findings demonstrate\nthe kind of output that justifies\nspending time reading source code.\u201d',
     "-- v1 synthesis", C_ACCENT),
]

y = 10.5
for quote, attrib, color in quotes:
    # Quote background
    rect = mpatches.FancyBboxPatch((1, y - 2.2), 8, 2.8, boxstyle="round,pad=0.4",
                                    facecolor='#1E293B', edgecolor=color, linewidth=2)
    ax.add_patch(rect)
    # Left accent bar
    rect2 = mpatches.FancyBboxPatch((1, y - 2.2), 0.15, 2.8, boxstyle="square,pad=0",
                                     facecolor=color, edgecolor='none')
    ax.add_patch(rect2)
    ax.text(5, y - 0.5, quote, fontsize=15, ha='center', va='center',
            color=C_TEXT, style='italic', linespacing=1.5)
    ax.text(8.5, y - 2.0, attrib, fontsize=12, ha='right', va='center', color=color)
    y -= 3.5

# Bottom conclusion
ax.text(5, 0.8, "结论: 结构帮验证, 自由帮洞察\n不该用同一个格式",
        fontsize=18, ha='center', va='center', fontweight='bold',
        color=C_ACCENT, linespacing=1.8)

plt.tight_layout()
fig.savefig(OUT / "03-blind-eval-quotes.png", dpi=200, bbox_inches='tight')
plt.close()

print(f"Generated 3 images in {OUT}/")
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name}")
