# Publishing Gate

全景框架实例化：Template → Procedure → QC → Enforcement。
每个渠道一个 template，统一 procedure，独立 QC，hook 阻断。

---

## Templates (WHAT shape — QC 的尺子)

### Substack Issue Template

```
# Issue #N: [One-sentence hook]

[Opening: 3 sentences max. What I found this week. No throat-clearing.]

## [Core discovery — one concept, not three]

[Explanation with specific evidence from source code or MOOC lecture.
Must include at least ONE of: code snippet, file path, line number.]

## What This Means

[1 paragraph: so what? Why should the reader care?]

## Next Week

[1 sentence preview]

---
Code: github.com/zl190/nano-agent-anatomy
```

**Constraints:**
- 800-1200 words (5 min read)
- One concept per issue — if you're covering two topics, split into two issues
- Must reference specific source file or MOOC lecture (no vague "the leaked code shows...")
- No AI smell: no "it's worth noting", no "moreover", no "in conclusion"
- End with code link, not a motivational closer

### Gumroad Product Template

```
[Product name]
[Price]
[One-paragraph pitch — problem → solution → what you get]

**What's inside:**
- [Bullet list of deliverables with specific quantities]

**Who this is for / not for:**
- For: [specific audience]
- Not for: [who should skip this]
```

**Constraints:**
- Pitch ≤ 100 words
- Every claim must be verifiable (don't say "comprehensive" — say "4 layers, 6 notes, 400 lines")
- No hype words: revolutionary, game-changing, unlock, unleash

### 小红书 Post Template

```
## 标题
[12字以内，有 hook]

## 正文
[第一句：事实或数据，不是观点]
[核心内容：一个发现，带证据]
[最后：CTA — repo 链接]

## Tags
[5-8 个，混合大词和长尾]

## 图片
[3张：架构图 + 代码截图 + 一个数据/对比]
```

**Constraints:**
- 正文 ≤ 300 字
- 第一句必须是事实（数字、日期、事件），不是"我觉得"
- 不夸大：fact-check 过的 claim 才能用
- 图片必须深色背景（匹配 blog 视觉风格）

---

## Procedure (WHEN/SEQUENCE)

```
1. WRITE    — 用 template 生成内容（builder）
2. FACT     — 每个 factual claim 标注来源（builder）
3. QC       — 独立 context 审查（reviewer, 不是 builder）
4. FIX      — 修 QC 发现的问题（builder）
5. PUBLISH  — 发布到渠道
6. VERIFY   — 发布后检查渲染/链接是否正常
```

**Rule: Step 3 必须在独立 context 里跑。** 写内容的 agent 不能审自己的内容。

---

## QC Checklist (per channel)

### All Channels

- [ ] **Fact check:** Every specific number has a source (no "41,500 forks" without citation)
- [ ] **AI smell scan:** Read aloud. Flag hedge cascades, empty emphasis, transition filler
- [ ] **Claim scope:** "CLI source code" not "entire source code" (unless qualified)
- [ ] **One concept:** Each piece covers one thing. If it covers two, split.
- [ ] **CTA exists:** Reader knows where to go next (repo, subscribe, etc.)

### Substack-specific

- [ ] **Word count:** 800-1200
- [ ] **Source reference:** At least one specific file/line/lecture cited
- [ ] **Hook test:** Would you open this email based on the subject line alone?

### 小红书-specific

- [ ] **字数:** ≤ 300
- [ ] **首句:** 是事实不是观点
- [ ] **图片:** 3张，深色背景，无 AI 生成文字
- [ ] **不夸大:** "1/5" 改成了 "2 layers undertaught" (fact-checked)

### Gumroad-specific

- [ ] **Deliverables specific:** 数量明确，不用模糊词
- [ ] **Price justified:** 免费版和付费版的区别清晰
- [ ] **No overpromise:** 只卖已完成的内容，预售标明出货时间

---

## Enforcement

### Pre-publish hook (manual for now, automate later)

在发布任何内容之前，运行：

```bash
# From nano-agent-anatomy root
./publish/qc-check.sh <channel> <file>
# Example: ./publish/qc-check.sh substack publish/substack-issue-0.md
```

Blocks publish if:
1. Word count out of range
2. No source citations found
3. AI smell patterns detected
4. File not in publish/ directory

### Future: CC hook integration

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Write",
      "type": "prompt",
      "prompt": "Check if the file being written is in publish/. If yes, verify it passes the QC checklist in publish/PUBLISH_GATE.md. If any check fails, exit 2."
    }]
  }
}
```
