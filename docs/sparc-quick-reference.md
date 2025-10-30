# SPARC Quick Reference Card

## 5 Core Phases

| Phase | Purpose | Key Output | Time |
|-------|---------|------------|------|
| **S**pecification | Define requirements | Requirements doc with acceptance criteria | 2-4h |
| **P**seudocode | Design algorithms | Language-agnostic algorithms + complexity | 1-2h |
| **A**rchitecture | System design | Component design + API contracts | 2-3h |
| **R**efinement | TDD implementation | Tested, optimized code | 8-16h |
| **C**ompletion | Integration + deploy | Production-ready system | 2-4h |

## 18 Specialized Modes

### 🔨 Development
- **Coder**: Feature implementation, batch operations
- **TDD**: Test-first development, coverage optimization
- **Tester**: Comprehensive testing, parallel execution

### 📋 Analysis & Design
- **Researcher**: Deep research, web searches, memory coordination
- **Architect**: System design, scalability planning
- **Designer**: UI/UX design, design systems

### ✅ Quality & Optimization
- **Reviewer**: Code review, security checks
- **Optimizer**: Performance tuning, bottleneck fixes
- **Debugger**: Bug investigation and fixes
- **Analyzer**: Deep code analysis, metrics

### 📚 Documentation
- **Documenter**: API docs, guides, README files

### 🎯 Orchestration
- **SPARC Coordinator**: Full SPARC workflow orchestration
- **Batch Executor**: Parallel task execution
- **Workflow Manager**: Complex workflow coordination
- **Memory Manager**: Cross-agent state management
- **Swarm Coordinator**: Multi-agent orchestration

### 💡 Innovation
- **Innovator**: Creative problem-solving, prototypes

## Quality Gates

```
Specification ✓→ Pseudocode ✓→ Architecture ✓→ Refinement ✓→ Completion ✓→ Deploy
    Gate 1          Gate 2          Gate 3         Gate 4         Gate 5
```

| Gate | Check | Requirement |
|------|-------|-------------|
| 1 | Spec → Pseudo | Requirements documented, approved |
| 2 | Pseudo → Arch | Algorithms validated, complexity analyzed |
| 3 | Arch → Refine | Design complete, security reviewed |
| 4 | Refine → Complete | Tests pass, coverage >80%, quality high |
| 5 | Complete → Deploy | Integration tests, docs, monitoring ready |

## Common Workflows

### New Feature (Full SPARC)
```
1. Specification (2-4h)   → Requirements + acceptance criteria
2. Pseudocode (1-2h)      → Algorithms + complexity
3. Architecture (2-3h)    → System design + APIs
4. Refinement (8-16h)     → TDD: Red → Green → Refactor
5. Completion (2-4h)      → Integration + docs + deploy
```

### Bug Fix (Light SPARC)
```
1. Light Spec (30m)       → Reproduce + define fix
2. Skip Pseudocode        → Not needed
3. Light Arch (15m)       → Verify components
4. Refinement (2-4h)      → Regression test + fix
5. Quick Complete (30m)   → Test suite + hotfix deploy
```

### Refactoring (Architecture Focus)
```
1. Specification (1-2d)   → Current state + goals
2. Pseudocode (1d)        → Migration algorithms
3. Architecture (2-3d)    → New design + migration plan
4. Iterative Refine (weeks) → Incremental changes + tests
5. Gradual Complete (1w)  → Cutover + monitoring
```

## Activation Patterns

### MCP Tools (Preferred in Claude Code)
```javascript
mcp__claude-flow__sparc_mode {
  mode: "coder",
  task_description: "implement feature X",
  options: { test_driven: true }
}
```

### CLI (Terminal/Fallback)
```bash
npx claude-flow sparc run <mode> "<task>"
npx claude-flow sparc tdd "<feature>"
npx claude-flow sparc modes  # List all modes
```

## Agent Coordination

### Memory Pattern
```bash
# Store phase outputs
memory_store "spec_complete_$(date +%s)" "Requirements done"

# Retrieve for next phase
memory_search "spec_complete" | tail -1
```

### Hooks Pattern
```bash
# Before work
npx claude-flow@alpha hooks pre-task --description "Task"
npx claude-flow@alpha hooks session-restore --session-id "sparc-X"

# After work
npx claude-flow@alpha hooks post-task --task-id "X"
npx claude-flow@alpha hooks session-end --export-metrics true
```

### Parallel Execution
```javascript
// ✅ CORRECT: Single message, all operations
[Single Message]:
  Task("Agent 1", "Task 1", "type1")
  Task("Agent 2", "Task 2", "type2")
  Task("Agent 3", "Task 3", "type3")

  TodoWrite { todos: [8-10 todos] }

  Write "file1.js"
  Write "file2.js"
  Write "file3.js"

// ❌ WRONG: Multiple messages
Message 1: Task("Agent 1")
Message 2: Task("Agent 2")  // Breaks coordination!
```

## Mode Selection Matrix

| Task | Primary Mode | Support Modes |
|------|-------------|---------------|
| New feature | SPARC Coordinator | Coder, Tester, Documenter |
| Bug fix | Debugger | Tester, Reviewer |
| Performance issue | Optimizer | Analyzer, Reviewer |
| Refactoring | Architect | Reviewer, Tester |
| Code review | Reviewer | Analyzer |
| Documentation | Documenter | Researcher |
| Research task | Researcher | Memory Manager |
| System design | Architect | Researcher, Designer |
| Testing | Tester | TDD, Reviewer |
| Multi-component | Swarm Coordinator | Multiple agents |

## TDD Cycle (Refinement Phase)

```
┌─────────────────────────────────────┐
│  1. RED: Write failing test         │
│     ↓                                │
│  2. GREEN: Minimal code to pass     │
│     ↓                                │
│  3. REFACTOR: Improve quality       │
│     ↓                                │
│  4. Repeat until feature complete   │
└─────────────────────────────────────┘
```

## Key Principles

### ✅ DO
- Follow all 5 phases for new features
- Write tests before implementation
- Analyze complexity in Pseudocode phase
- Design for scalability in Architecture
- Use parallel execution for independent tasks
- Enforce quality gates
- Document decisions in memory

### ❌ DON'T
- Skip phases (except simple bug fixes)
- Rush to implementation without planning
- Ignore complexity analysis
- Over-engineer solutions
- Skip tests to save time
- Ignore quality gates
- Work in isolation without coordination

## Success Metrics

### Phase Metrics
- **Specification**: Requirements completeness
- **Pseudocode**: Algorithm efficiency (O notation)
- **Architecture**: Design clarity, scalability score
- **Refinement**: Code coverage (>80%), quality score
- **Completion**: Documentation coverage, deployment success

### Overall Metrics
- Time per phase
- Quality gate pass rate
- Defect discovery timing (earlier = better)
- Methodology compliance
- Team velocity

## Common Pitfalls

| Pitfall | Impact | Prevention |
|---------|--------|------------|
| Skipping specification | Unclear requirements → rework | Enforce Gate 1 |
| No complexity analysis | Inefficient algorithms → performance issues | Mandatory in Pseudocode |
| Weak architecture | Scalability problems → rewrites | Thorough design review |
| Skipping tests | Bugs in production → incidents | TDD enforcement |
| Poor documentation | Knowledge loss → maintenance hell | Completion gate |

## Resource Links

- **Full Guide**: [SPARC Modes Reference](./sparc-modes-reference.md)
- **Project Setup**: [CLAUDE.md](../CLAUDE.md)
- **Mode Details**: `.claude/commands/sparc/*.md`
- **Agent Templates**: `.claude/agents/sparc/*.md`

---

**Pro Tip**: For complex projects, use SPARC Coordinator to orchestrate the entire workflow. For focused tasks, choose specialized modes directly.

**Remember**: Quality gates are non-negotiable. Each phase builds on the previous one. Skipping steps = technical debt.
