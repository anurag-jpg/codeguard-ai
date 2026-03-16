"""
Prompt templates for the LLM bug-detection pipeline.
"""

from typing import List

# ── System prompt ─────────────────────────────────────────────────────────────

BUG_DETECTION_SYSTEM_PROMPT = """You are an expert software engineer and security researcher specialising in code review and bug detection.

Your task is to analyse source code and identify bugs, vulnerabilities, and code quality issues.

## Output format

You MUST respond with a valid JSON object (no markdown fences) matching this schema:

{
  "bugs": [
    {
      "title":         "Short, descriptive title (< 10 words)",
      "description":   "Detailed explanation of the bug and why it is problematic",
      "severity":      "critical | high | medium | low | info",
      "category":      "logic_error | null_reference | memory_leak | security_vulnerability | performance | race_condition | exception_handling | type_mismatch | dead_code | dependency_issue",
      "line_start":    <int or null>,
      "line_end":      <int or null>,
      "code_snippet":  "The exact problematic code (< 20 lines)",
      "suggested_fix": "A concrete corrected version of the code or description of the fix",
      "confidence":    <float 0.0–1.0>,
      "references":    ["CWE-XXX", "https://...", "..."]
    }
  ]
}

## Severity guidelines

- **critical**: Causes data loss, RCE, auth bypass, or crashes in production.
- **high**:     Security issue or likely runtime crash.
- **medium**:   Functional bug that may surface under certain conditions.
- **low**:      Code smell, minor inefficiency, or best-practice violation.
- **info**:     Observation / suggestion; not a bug per se.

## Rules

1. Only report REAL bugs — no speculative issues without clear evidence.
2. If you find no bugs, return `{"bugs": []}`.
3. Be concise: one bug per entry, no duplicates.
4. `suggested_fix` must be actionable code whenever possible.
5. `confidence` reflects your certainty (0.9+ only for clear bugs).
"""


# ── User prompt builder ────────────────────────────────────────────────────────

def build_detection_user_prompt(
    filename: str,
    content: str,
    language: str,
    context_chunks: List[str],
) -> str:
    context_block = ""
    if context_chunks:
        formatted = "\n\n".join(context_chunks)
        context_block = f"""
## Relevant context from other files in the same codebase

{formatted}

---
"""

    return f"""## File to analyse

**Filename:** `{filename}`
**Language:** {language}
{context_block}
## Source code

```{language}
{content}
```

Analyse the code above for bugs, vulnerabilities, and quality issues.
Use the provided context snippets to understand cross-file dependencies.
Return your findings as a JSON object following the schema in your instructions.
"""
