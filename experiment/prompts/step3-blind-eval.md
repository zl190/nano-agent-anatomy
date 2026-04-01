You are an independent evaluator for a source code reading experiment. You will compare two sets of outputs (labeled A and B) from reading the same 513K-line TypeScript codebase. You do NOT know which methodology produced which output.

## Your task

1. Read the anonymized outputs:
   - /Users/zl190/Developer/personal/nano-agent-anatomy/experiment/blind/A/
   - /Users/zl190/Developer/personal/nano-agent-anatomy/experiment/blind/B/

   Each directory contains 6 reader outputs + 1 synthesis.

2. Read the evaluation rubric:
   /Users/zl190/Developer/personal/nano-agent-anatomy/experiment/blind-eval-rubric.md

3. For each reader pair (A-reader-1 vs B-reader-1, etc.), score on the rubric dimensions.

4. For the synthesis pair (A-synthesis vs B-synthesis), score on rubric dimensions.

5. Compute automated metrics for both sets:
   - Can each reader output be parsed as valid JSON? (yes/no per reader)
   - Count: symbols extracted, patterns identified, evidence citations (file:line refs), surprises noted
   - Check: are confidence levels present on claims?

6. Write your evaluation to:
   /Users/zl190/Developer/personal/nano-agent-anatomy/experiment/eval/blind-eval-results.json

   Format:
   ```json
   {
     "evaluator_note": "Brief note on your evaluation approach",
     "per_reader_scores": [
       {
         "reader_id": 1,
         "A": {"extraction_completeness": N, "pattern_depth": N, "evidence_quality": N, "cross_reference_quality": N, "actionability": N},
         "B": {"extraction_completeness": N, "pattern_depth": N, "evidence_quality": N, "cross_reference_quality": N, "actionability": N},
         "preference": "A or B",
         "rationale": "why"
       }
     ],
     "synthesis_scores": {
       "A": {"extraction_completeness": N, "pattern_depth": N, "evidence_quality": N, "cross_reference_quality": N, "actionability": N},
       "B": {"extraction_completeness": N, "pattern_depth": N, "evidence_quality": N, "cross_reference_quality": N, "actionability": N},
       "preference": "A or B",
       "rationale": "why"
     },
     "automated_metrics": {
       "A": {"json_parseable_readers": N, "total_symbols": N, "total_patterns": N, "total_evidence_citations": N, "total_surprises": N, "has_confidence_tags": bool},
       "B": {"json_parseable_readers": N, "total_symbols": N, "total_patterns": N, "total_evidence_citations": N, "total_surprises": N, "has_confidence_tags": bool}
     },
     "overall_preference": "A or B",
     "overall_rationale": "detailed explanation"
   }
   ```

7. Write experiment/eval/DONE when complete.

IMPORTANT: Do NOT try to guess which output is v1 or v2. Evaluate purely on quality.
