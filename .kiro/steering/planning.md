---
inclusion: manual
---

# Planning Skill

Activate this skill when implementing complex features, architectural changes, or multi-step refactoring.

## Planning Process

### 1. Requirements Analysis
- Understand the feature request completely
- Identify success criteria
- List assumptions and constraints
- Ask clarifying questions if anything is ambiguous

### 2. Architecture Review
- Analyze existing codebase structure
- Identify affected components and files
- Review similar implementations for patterns to follow
- Consider reusable code and shared utilities

### 3. Step Breakdown
For each step, define:
- Clear, specific action
- File paths and locations
- Dependencies on other steps
- Estimated complexity (Low/Medium/High)
- Potential risks

### 4. Implementation Order
- Prioritize by dependencies (do prerequisites first)
- Group related changes to minimize context switching
- Enable incremental testing at each phase

## Plan Template

```markdown
# Implementation Plan: [Feature Name]

## Overview
[2-3 sentence summary of what we're building and why]

## Affected Files
- [file path] — [what changes]

## Implementation Phases

### Phase 1: [Foundation]
1. [Step] (File: path/to/file)
   - Action: What to do
   - Dependencies: None / Requires step X
   - Risk: Low/Medium/High

### Phase 2: [Core Logic]
...

### Phase 3: [Integration & Polish]
...

## Testing Strategy
- Unit: [what to test]
- Integration: [what flows to test]
- E2E: [what user journeys to test]

## Risks & Mitigations
- Risk: [description] → Mitigation: [how to handle]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
```

## Rules

- Be specific: use exact file paths, function names, variable names
- Think about edge cases and error scenarios
- Minimize changes: extend existing code over rewriting
- Follow existing project conventions
- Each step should be independently verifiable
