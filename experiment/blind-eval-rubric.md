# Blind Evaluation Rubric

Score each dimension 1-5. Be strict — 5 is exceptional, 3 is adequate, 1 is poor.

## Dimensions

### 1. Extraction Completeness (1-5)
- 5: All major classes, interfaces, functions, and types extracted with accurate signatures
- 3: Most important symbols captured, some gaps in secondary files
- 1: Only superficial listing, many important symbols missed

### 2. Pattern Depth (1-5)
- 5: Patterns are non-obvious production insights that would change how you build software
- 3: Patterns are accurate but could be guessed from reading documentation
- 1: Patterns are surface-level descriptions of what the code does (not insights)

### 3. Evidence Quality (1-5)
- 5: Every claim references specific file:line ranges, verifiable against source
- 3: Some claims have file references, others are unsupported
- 1: No specific evidence, claims are generic assertions

### 4. Cross-Reference Quality (1-5)
- 5: Connections between subsystems traced with specific data flow descriptions
- 3: Some cross-references noted but not traced in detail
- 1: Each file analyzed in isolation, no connections identified

### 5. Actionability (1-5)
- 5: A senior engineer could navigate the codebase confidently using this output alone
- 3: Useful as a starting point but would need significant additional exploration
- 1: Not useful for navigation — too generic or too verbose to be practical

## Overall Preference
After scoring all dimensions, state which output set (A or B) you would prefer as a codebase guide, and explain why in 2-3 sentences.
