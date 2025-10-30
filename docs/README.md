# Project Documentation

## SPARC Methodology Documentation

This directory contains comprehensive documentation for the SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology implementation in this project.

### 📚 Documentation Files

#### 1. [SPARC Modes Reference](./sparc-modes-reference.md)
**Complete reference guide covering:**
- Overview of SPARC methodology
- Detailed breakdown of all 5 phases
- Comprehensive guide to 18 specialized modes
- Workflow patterns and examples
- Best practices and quality gates
- Integration examples

**Use this when:** You need complete understanding of SPARC methodology, phase details, or mode capabilities.

---

#### 2. [SPARC Quick Reference](./sparc-quick-reference.md)
**Quick lookup card with:**
- 5 phases overview table
- 18 modes summary
- Quality gates checklist
- Common workflows
- Activation patterns
- Mode selection matrix
- TDD cycle
- Key principles

**Use this when:** You need quick reference during development, want to check quality gates, or select the right mode.

---

#### 3. [SPARC Workflows](./sparc-workflows.md)
**Detailed workflow examples:**
- Complete feature development (Authentication system)
- Bug fix workflow (Session expiry bug)
- Architecture refactoring (Monolith to microservices)
- Parallel component development (E-commerce platform)
- Research-driven development (ML recommendation engine)
- Performance optimization
- Security enhancement
- Documentation sprint

**Use this when:** You're planning a project and want to see concrete examples of SPARC in action.

---

## Quick Navigation

### I want to...

**Learn SPARC methodology:**
→ Start with [SPARC Modes Reference](./sparc-modes-reference.md#overview)

**Implement a new feature:**
→ Check [SPARC Workflows - Complete Feature Development](./sparc-workflows.md#complete-feature-development)

**Fix a bug:**
→ Check [SPARC Workflows - Bug Fix Workflow](./sparc-workflows.md#bug-fix-workflow)

**Find the right mode:**
→ Check [Mode Selection Matrix](./sparc-quick-reference.md#mode-selection-matrix)

**Understand quality gates:**
→ Check [Quality Gates](./sparc-quick-reference.md#quality-gates)

**See activation commands:**
→ Check [Activation Patterns](./sparc-quick-reference.md#activation-patterns)

**Get quick answers:**
→ Use [SPARC Quick Reference](./sparc-quick-reference.md)

---

## SPARC at a Glance

### The 5 Phases

```
┌─────────────────────────────────────────────────────────────┐
│                    SPARC Methodology                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SPECIFICATION  →  Define requirements & acceptance     │
│         ↓                                                   │
│  2. PSEUDOCODE     →  Design algorithms & logic            │
│         ↓                                                   │
│  3. ARCHITECTURE   →  System design & components           │
│         ↓                                                   │
│  4. REFINEMENT     →  TDD implementation & optimization    │
│         ↓                                                   │
│  5. COMPLETION     →  Integration & deployment             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The 18 Modes

**Development (3):** Coder • TDD • Tester
**Analysis (3):** Researcher • Architect • Designer
**Quality (4):** Reviewer • Optimizer • Debugger • Analyzer
**Documentation (1):** Documenter
**Orchestration (6):** SPARC Coordinator • Batch Executor • Workflow Manager • Memory Manager • Swarm Coordinator
**Innovation (1):** Innovator

---

## Integration with Project

### Project Setup
See [../CLAUDE.md](../CLAUDE.md) for:
- MCP server configuration
- Agent coordination setup
- Hook integration
- Memory management

### Agent Templates
Located in `/.claude/agents/sparc/`:
- specification.md
- pseudocode.md
- architecture.md
- refinement.md

### Command Templates
Located in `/.claude/commands/sparc/`:
- 18 mode command files
- Each with activation patterns
- MCP tool integration examples

---

## Best Practices Summary

### ✅ DO
- Follow all 5 phases for new features
- Write tests before implementation (TDD)
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

---

## Success Metrics

**Quality Indicators:**
- Test coverage >80%
- Code quality score A+
- <200ms p95 response time
- 0 critical security vulnerabilities
- Complete documentation

**Process Metrics:**
- All quality gates passed
- Phase completion times tracked
- Defect discovery timing (earlier = better)
- Methodology compliance >95%

---

## Additional Resources

### External Links
- [Claude-Flow GitHub](https://github.com/ruvnet/claude-flow)
- [SPARC Methodology](https://github.com/ruvnet/claude-flow#sparc-methodology)
- [NestJS Documentation](https://docs.nestjs.com/)

### Project Files
- Main Configuration: [CLAUDE.md](../CLAUDE.md)
- Git Ignore: [.gitignore](../.gitignore)
- Package Config: [package.json](../package.json)

---

## Changelog

### 2025-10-30
- Initial SPARC documentation created
- Comprehensive reference guide (42+ pages)
- Quick reference card (5 pages)
- Detailed workflow examples (15+ pages)
- 18 specialized modes documented
- 5 phases fully explained
- Integration examples added

---

## Contributing

When updating SPARC documentation:

1. **Update all three files** for consistency:
   - sparc-modes-reference.md (detailed)
   - sparc-quick-reference.md (quick lookup)
   - sparc-workflows.md (examples)

2. **Follow structure**:
   - Clear headers and table of contents
   - Code examples with syntax highlighting
   - Use tables for comparisons
   - Include quality gate checklists

3. **Version changes**:
   - Update changelog in this README
   - Update "Last Updated" dates
   - Document breaking changes

---

## Questions & Support

**For SPARC methodology questions:**
- Review the comprehensive [Modes Reference](./sparc-modes-reference.md)
- Check [workflow examples](./sparc-workflows.md)
- See [quick reference](./sparc-quick-reference.md)

**For project-specific questions:**
- Check [CLAUDE.md](../CLAUDE.md) for configuration
- Review agent templates in `.claude/agents/sparc/`
- Check command files in `.claude/commands/sparc/`

**For issues:**
- GitHub Issues: [project-b-blueprint/issues](https://github.com/project-b-blueprint/issues)
- Claude-Flow Issues: [claude-flow/issues](https://github.com/ruvnet/claude-flow/issues)

---

*This documentation is part of the Project B Blueprint SPARC implementation.*
*Last Updated: 2025-10-30*
