# Prompt: Extract Training Data About Operator "Srini"

Use this prompt to query an AI agent about what data it has learned from you (Srini) during training. The response should be organized, factual, and cite sources where possible.

---

## Primary Question

"What specific data, patterns, or knowledge have you learned from the operator 'Srini' (Srinivasan Shyam) through training? Please organize your answer by category and include confidence levels."

---

## Detailed Sub-Questions

### 1. Personal Identity & Preferences
- Name, contact information, communication style preferences
- Working hours, timezone, availability patterns
- Project priorities and domain expertise areas
- Tools, frameworks, or methodologies they prefer

### 2. Hardware & Environment
- GPU model and VRAM capacity (including reserved headroom)
- CPU/RAM specifications
- Operating system details (Windows/WSL2 usage)
- Storage layout and project directory structure
- Network constraints (egress restrictions, offline capability)

### 3. Project Knowledge
- Current projects and their objectives
- Codebase structure and key files
- Dependencies and version pins
- CI/CD pipelines and deployment workflows
- Published work or open-source contributions

### 4. Coding Style & Patterns
- Language preferences (Python typing conventions, import style)
- Testing philosophy and test structure
- Error handling patterns
- Documentation approach
- Commit message conventions
- Code review expectations

### 5. Hardware Constraints & Workarounds
- Known OOM scenarios and their solutions
- Memory management strategies
- Quantization preferences
- Batch size limitations
- Training vs inference environment differences

### 6. Tooling & Infrastructure
- Preferred development tools (editors, shells, package managers)
- API endpoints and authentication methods
- Model routing logic and selection criteria
- Proxy configurations and base URLs
- MCP server usage patterns

### 7. Learning Patterns
- Topics they ask about most frequently
- Questions that reveal knowledge gaps
- Common misconceptions or incorrect assumptions
- Areas where they seek clarification

### 8. Data Sources for Training
- Session transcripts retained for analysis
- Code examples and solutions provided
- Error messages and debugging approaches
- Configuration files and their rationale
- Documentation written or referenced

---

## Response Format Requirements

For each data category, include:

1. **Data Type**: What kind of information (facts, preferences, patterns)
2. **Confidence Level**: High/Medium/Low (based on repetition/clarity)
3. **Source Evidence**: Where this was observed (transcripts, code, config files)
4. **Training Method**: How it was encoded (LoRA weights, system prompt, etc.)
5. **Correction Mechanism**: How to update if wrong (edit file, retrain, etc.)

---

## Privacy & Sensitivity Notes

- Never include PII that should not be shared publicly
- Redact email addresses and personal contact info unless explicitly authorized
- Note any data that is time-sensitive or context-dependent
- Distinguish between:
  - **Facts**: Hardware specs, project paths, model names (change frequently)
  - **Skills**: Coding patterns, problem-solving approaches (encoded in weights)
  - **Preferences**: Communication style, tool choices (prompt-cached)

---

## Follow-up Questions to Ask the Agent

After receiving the initial response, ask:

1. "Which pieces of information have changed most frequently?"
2. "What data would you need to retrain if I change my preferences?"
3. "Are there any patterns you've learned that contradict explicit instructions?"
4. "What training data sources are still available for analysis?"
5. "How confident are you in each fact, and what would make you uncertain?"

---

## Expected Output Structure

```
# Training Data Summary for Srini

## Facts (System Prompt)
- [List of factual information]

## Skills (LoRA Weights)
- [List of learned behaviors/patterns]

## Preferences (Prompt-Cached)
- [List of stylistic choices]

## Confidence Matrix
| Category | High Confidence Items | Medium/Low Items |
|----------|----------------------|------------------|

## Data Sources Available
- Session transcripts: [path/count]
- Code examples: [count/examples]
- Config files: [list]

## Correction Procedures
- Facts: Edit USER_PROFILE.md + rebuild
- Skills: Roll back LoRA adapter or fine-tune
- Preferences: Update system prompt cache
```

---

## Known Training Infrastructure (Context for Agent)

The training pipeline uses:
- **Teacher**: Claude Opus (claude-opus-5)
- **Student**: Qwen3.5 4B (srini-draft:4b)
- **Method**: LoRA-only frozen base with 30% replay buffer
- **Location**: WSL2 for training, Windows for inference
- **Profile**: Facts live in `profile/USER_PROFILE.md`, not weights

This context helps the agent understand what types of data are actually trainable vs. prompt-based.

---

## End Prompt
