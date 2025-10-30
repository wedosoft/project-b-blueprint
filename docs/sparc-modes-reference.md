# SPARC Methodology Reference Guide

**Version:** 2.0.0
**Last Updated:** 2025-10-30

## Table of Contents
1. [Overview](#overview)
2. [Core SPARC Phases](#core-sparc-phases)
3. [SPARC Modes](#sparc-modes)
4. [Workflow Patterns](#workflow-patterns)
5. [Best Practices](#best-practices)
6. [Integration Examples](#integration-examples)

---

## Overview

### What is SPARC?

SPARC is a systematic software development methodology that ensures high-quality, maintainable code through five distinct phases:

- **S**pecification - Requirements gathering and acceptance criteria
- **P**seudocode - Algorithm design and logic planning
- **A**rchitecture - System design and component definition
- **R**efinement - Test-driven implementation and optimization
- **C**ompletion - Integration, documentation, and deployment

### Why Use SPARC?

**Quality Assurance**: Each phase has clear deliverables and quality gates
**Systematic Approach**: Prevents rushing to implementation without planning
**Test-Driven**: Emphasizes TDD for reliable, maintainable code
**Scalability**: Works for projects from small features to large systems
**Traceability**: Complete audit trail from requirements to deployment

### Project Implementation

This project implements SPARC with:
- **Claude-Flow orchestration** for parallel execution
- **Memory-based coordination** for cross-agent collaboration
- **Automated hooks** for quality enforcement
- **18 specialized modes** for different development needs

---

## Core SPARC Phases

### 1. Specification Phase

**Purpose**: Define clear, testable requirements before writing code

**Responsibilities**:
- Functional requirements documentation
- Non-functional requirements (performance, security)
- Use case definition with preconditions/postconditions
- Acceptance criteria in Gherkin format
- Edge case identification
- Data model specification
- API contract definition

**Deliverables**:
```yaml
specification:
  functional_requirements:
    - id: "FR-001"
      description: "System shall authenticate users via OAuth2"
      priority: "high"
      acceptance_criteria:
        - "Users can login with Google/GitHub"
        - "Session persists for 24 hours"
        - "Refresh tokens auto-renew"

  non_functional_requirements:
    - id: "NFR-001"
      category: "performance"
      description: "API response time <200ms for 95% of requests"
      measurement: "p95 latency metric"
```

**Quality Gate**: All requirements documented, stakeholders approved, acceptance criteria clear

**Best Practices**:
- Make requirements specific and measurable (avoid "fast" or "user-friendly")
- Every requirement must have testable acceptance criteria
- Document edge cases and error scenarios
- Consider the full user journey from start to finish
- Get stakeholder validation early

---

### 2. Pseudocode Phase

**Purpose**: Design efficient algorithms independent of implementation language

**Responsibilities**:
- Algorithm design with clear logic flow
- Data structure selection and justification
- Time/space complexity analysis
- Design pattern identification
- Optimization opportunities

**Deliverables**:
```
ALGORITHM: AuthenticateUser
INPUT: email (string), password (string)
OUTPUT: user (User object) or error

BEGIN
    // Validate inputs
    IF email is empty OR password is empty THEN
        RETURN error("Invalid credentials")
    END IF

    // Retrieve user from database
    user ← Database.findUserByEmail(email)

    IF user is null THEN
        RETURN error("User not found")
    END IF

    // Verify password
    isValid ← PasswordHasher.verify(password, user.passwordHash)

    IF NOT isValid THEN
        SecurityLog.logFailedLogin(email)
        RETURN error("Invalid credentials")
    END IF

    // Create session
    session ← CreateUserSession(user)

    RETURN {user: user, session: session}
END

COMPLEXITY ANALYSIS:
- Time: O(log n) - database lookup with index
- Space: O(1) - constant space for user object
```

**Quality Gate**: Algorithms validated, complexity analyzed, patterns identified

**Best Practices**:
- Use language-agnostic syntax
- Focus on logic flow, not implementation details
- Always analyze time/space complexity
- Break complex algorithms into subroutines
- Document optimization opportunities

---

### 3. Architecture Phase

**Purpose**: Transform algorithms into scalable system designs

**Responsibilities**:
- High-level system architecture
- Component definition and boundaries
- Interface contracts and APIs
- Data architecture and schemas
- Infrastructure planning
- Security architecture
- Scalability design

**Deliverables**:
```yaml
components:
  auth_service:
    name: "Authentication Service"
    type: "Microservice"
    technology:
      language: "TypeScript"
      framework: "NestJS"
      runtime: "Node.js 18"

    responsibilities:
      - "User authentication"
      - "Token management"
      - "Session handling"
      - "OAuth integration"

    interfaces:
      rest:
        - POST /auth/login
        - POST /auth/logout
        - GET /auth/verify

      grpc:
        - VerifyToken(token) -> User

      events:
        publishes: [user.logged_in, user.logged_out]
        subscribes: [user.deleted, user.suspended]

    dependencies:
      internal: [user_service]
      external: [postgresql, redis, rabbitmq]

    scaling:
      horizontal: true
      instances: "2-10"
      triggers:
        - cpu > 70%
        - memory > 80%
        - request_rate > 1000/sec
```

**Quality Gate**: Design approved, scalability planned, security reviewed

**Best Practices**:
- Design for failure (assume components will fail)
- Maintain loose coupling between components
- Keep high cohesion within components
- Build security into architecture, not as an afterthought
- Design for observability (monitoring, logging, tracing)

---

### 4. Refinement Phase

**Purpose**: Implement code using TDD with continuous quality improvement

**Responsibilities**:
- Test-Driven Development (Red-Green-Refactor)
- Code optimization
- Performance tuning
- Error handling enhancement
- Code refactoring
- Quality metrics tracking

**TDD Workflow**:

**Red Phase** - Write failing tests:
```typescript
describe('AuthenticationService', () => {
  it('should return user and token for valid credentials', async () => {
    // Arrange
    const credentials = { email: 'user@example.com', password: 'Pass123!' };
    mockUserRepo.findByEmail.mockResolvedValue(mockUser);

    // Act
    const result = await service.login(credentials);

    // Assert
    expect(result).toHaveProperty('user');
    expect(result).toHaveProperty('token');
  });
});
```

**Green Phase** - Make tests pass:
```typescript
async login(credentials: LoginDto): Promise<LoginResult> {
  const user = await this.userRepo.findByEmail(credentials.email);
  if (!user || !await this.verifyPassword(credentials.password, user.passwordHash)) {
    throw new UnauthorizedException('Invalid credentials');
  }

  const token = this.generateToken(user);
  return { user: this.sanitizeUser(user), token };
}
```

**Refactor Phase** - Improve code quality:
```typescript
async login(credentials: LoginDto): Promise<LoginResult> {
  await this.validateLoginAttempt(credentials.email);

  try {
    const user = await this.authenticateUser(credentials);
    const session = await this.createSession(user);

    await this.eventBus.emit('user.logged_in', { userId: user.id });

    return { user: this.sanitizeUser(user), token: session.token };
  } catch (error) {
    await this.handleLoginFailure(credentials.email, error);
    throw error;
  }
}
```

**Quality Gate**: Tests pass, coverage >80%, performance acceptable, no code smells

**Best Practices**:
- Always write tests before implementation
- Make small, incremental improvements
- Refactor continuously while keeping tests green
- Set and monitor performance budgets
- Plan for failure scenarios with retry logic and circuit breakers

---

### 5. Completion Phase

**Purpose**: Prepare system for production deployment

**Responsibilities**:
- Integration testing
- Documentation finalization
- Deployment preparation
- Performance validation
- Security audit
- Handoff procedures

**Deliverables**:
- Comprehensive test suite (unit, integration, E2E)
- API documentation
- Architecture diagrams
- Deployment runbooks
- Monitoring dashboards
- Security audit report

**Quality Gate**: All tests pass, documentation complete, production-ready

---

## SPARC Modes

### Core Development Modes

#### Coder Mode
**Purpose**: Autonomous code generation with batch operations

**Capabilities**:
- Feature implementation
- Code refactoring
- Bug fixes
- API development
- Algorithm implementation

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "coder",
  task_description: "implement user authentication",
  options: {
    test_driven: true,
    parallel_edits: true
  }
}
```

**Best For**:
- Implementing designed features
- Batch file operations
- Parallel code modifications
- Test-driven development

---

#### TDD Mode
**Purpose**: Test-driven development with comprehensive testing

**Capabilities**:
- Test-first development
- Red-green-refactor cycle
- Test suite design
- Coverage optimization
- Continuous testing

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "tdd",
  task_description: "shopping cart feature",
  options: {
    coverage_target: 90,
    test_framework: "jest"
  }
}
```

**Best For**:
- New feature development
- Critical system components
- Ensuring code reliability
- Establishing quality baseline

---

#### Tester Mode
**Purpose**: Comprehensive testing with parallel execution

**Capabilities**:
- Test planning
- Test execution
- Bug detection
- Coverage analysis
- Report generation

**Test Types**:
- Unit tests
- Integration tests
- E2E tests
- Performance tests
- Security tests

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "tester",
  task_description: "full regression suite",
  options: {
    parallel: true,
    coverage: true
  }
}
```

**Best For**:
- Regression testing
- Quality assurance
- Release validation
- Performance benchmarking

---

### Analysis & Design Modes

#### Researcher Mode
**Purpose**: Deep research with parallel web searches and memory coordination

**Capabilities**:
- Information gathering
- Source evaluation
- Trend analysis
- Competitive research
- Technology assessment

**Research Methods**:
- Parallel web searches
- Academic paper analysis
- Industry report synthesis
- Expert opinion gathering
- Data compilation

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "researcher",
  task_description: "research AI trends 2024",
  options: {
    depth: "comprehensive",
    sources: ["academic", "industry", "news"]
  }
}
```

**Best For**:
- Technology evaluation
- Market research
- Best practices discovery
- Architecture decisions

---

#### Architect Mode
**Purpose**: System design with memory-based coordination

**Capabilities**:
- System architecture design
- Component interface definition
- Database schema design
- API contract specification
- Infrastructure planning

**Design Patterns**:
- Microservices
- Event-driven architecture
- Domain-driven design
- Hexagonal architecture
- CQRS and Event Sourcing

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "architect",
  task_description: "design microservices architecture",
  options: {
    detailed: true,
    memory_enabled: true
  }
}
```

**Best For**:
- New system design
- Architecture refactoring
- Scalability planning
- Technology stack selection

---

#### Designer Mode
**Purpose**: UI/UX design with user-centered approach

**Capabilities**:
- Interface design
- User experience planning
- Design system creation
- Accessibility standards
- Responsive layouts

**Best For**:
- Frontend design
- Design systems
- User flow optimization
- Accessibility compliance

---

### Quality & Optimization Modes

#### Reviewer Mode
**Purpose**: Code review using batch file analysis

**Capabilities**:
- Code quality assessment
- Security review
- Performance analysis
- Best practices check
- Documentation review

**Review Criteria**:
- Code correctness
- Design patterns
- Error handling
- Test coverage
- Maintainability

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "reviewer",
  task_description: "review pull request #123",
  options: {
    security_check: true,
    performance_check: true
  }
}
```

**Best For**:
- Pull request reviews
- Code audits
- Security assessments
- Quality gates

---

#### Optimizer Mode
**Purpose**: Performance optimization and efficiency improvements

**Capabilities**:
- Performance profiling
- Bottleneck identification
- Algorithm optimization
- Resource efficiency
- Caching strategies

**Best For**:
- Performance tuning
- Resource optimization
- Scalability improvements
- Cost reduction

---

#### Debugger Mode
**Purpose**: Systematic bug investigation and resolution

**Capabilities**:
- Bug reproduction
- Root cause analysis
- Fix implementation
- Regression prevention
- Error logging

**Best For**:
- Production issues
- Complex bugs
- System failures
- Performance problems

---

### Documentation & Management Modes

#### Documenter Mode
**Purpose**: Comprehensive documentation with batch operations

**Capabilities**:
- API documentation
- Code documentation
- User guides
- Architecture docs
- README files

**Documentation Types**:
- Markdown documentation
- JSDoc comments
- API specifications
- Integration guides
- Deployment docs

**Activation**:
```javascript
mcp__claude-flow__sparc_mode {
  mode: "documenter",
  task_description: "create API documentation",
  options: {
    format: "markdown",
    include_examples: true
  }
}
```

**Best For**:
- API documentation
- Developer guides
- System documentation
- Knowledge transfer

---

#### Analyzer Mode
**Purpose**: Deep code and system analysis

**Capabilities**:
- Codebase analysis
- Dependency mapping
- Complexity metrics
- Technical debt assessment
- Security scanning

**Best For**:
- System audits
- Migration planning
- Architecture reviews
- Technical debt evaluation

---

### Orchestration Modes

#### SPARC Coordinator
**Purpose**: Orchestrate complete SPARC methodology workflow

**Capabilities**:
- Phase coordination
- Quality gate enforcement
- Agent orchestration
- Progress tracking
- Result synthesis

**Phase Transitions**:
```
Specification → Quality Gate 1 → Pseudocode
     ↓
Pseudocode → Quality Gate 2 → Architecture
     ↓
Architecture → Quality Gate 3 → Refinement
     ↓
Refinement → Quality Gate 4 → Completion
     ↓
Completion → Final Review → Deployment
```

**Best For**:
- Complete feature development
- New projects
- Systematic workflows
- Quality assurance

---

#### Batch Executor Mode
**Purpose**: Parallel execution of multiple tasks

**Capabilities**:
- Task parallelization
- Resource optimization
- Progress monitoring
- Result aggregation
- Error handling

**Best For**:
- Bulk operations
- Multi-file changes
- Parallel testing
- Mass updates

---

#### Workflow Manager Mode
**Purpose**: Complex workflow orchestration

**Capabilities**:
- Workflow design
- Task sequencing
- Dependency management
- State tracking
- Rollback handling

**Best For**:
- Multi-step processes
- CI/CD pipelines
- Release management
- Complex deployments

---

#### Memory Manager Mode
**Purpose**: Cross-agent memory and state management

**Capabilities**:
- State persistence
- Memory coordination
- Knowledge sharing
- Context preservation
- Session management

**Best For**:
- Long-running projects
- Multi-agent coordination
- Knowledge retention
- Session continuity

---

#### Swarm Coordinator Mode
**Purpose**: Multi-agent swarm orchestration

**Capabilities**:
- Agent spawning
- Task distribution
- Load balancing
- Result synthesis
- Failure recovery

**Best For**:
- Large-scale projects
- Parallel development
- Complex systems
- Distributed work

---

### Innovation Mode

#### Innovator Mode
**Purpose**: Creative problem-solving and novel solutions

**Capabilities**:
- Creative ideation
- Alternative approaches
- Innovation patterns
- Prototype development
- Experimentation

**Best For**:
- Novel problems
- Innovation projects
- Proof of concepts
- Exploratory development

---

## Workflow Patterns

### Pattern 1: Complete Feature Development

**Use Case**: Implement new authentication system

**Workflow**:
```
1. Specification Phase (2-4 hours)
   - Gather requirements
   - Define acceptance criteria
   - Document edge cases
   - Get stakeholder approval

2. Pseudocode Phase (1-2 hours)
   - Design authentication algorithm
   - Select data structures (LRU cache)
   - Analyze complexity
   - Identify patterns (Strategy, Observer)

3. Architecture Phase (2-3 hours)
   - Design microservice architecture
   - Define API contracts
   - Plan database schema
   - Design for scalability

4. Refinement Phase (8-16 hours)
   - Write failing tests (Red)
   - Implement minimal code (Green)
   - Refactor for quality (Refactor)
   - Optimize performance
   - Enhance error handling

5. Completion Phase (2-4 hours)
   - Run full test suite
   - Generate documentation
   - Deploy to staging
   - Performance validation
   - Security audit
```

**Agent Coordination**:
```javascript
// Phase 1-3: Sequential planning
Task("Specification agent", "Gather auth requirements...", "researcher")
→ Quality Gate 1 →
Task("Pseudocode agent", "Design auth algorithms...", "architect")
→ Quality Gate 2 →
Task("Architecture agent", "Design microservices...", "architect")
→ Quality Gate 3 →

// Phase 4: Parallel implementation
[Parallel execution]:
  Task("Backend coder", "Implement auth service", "coder")
  Task("Database coder", "Create schemas", "coder")
  Task("Test engineer", "Write test suite", "tester")
  Task("Security reviewer", "Security audit", "reviewer")

→ Quality Gate 4 →

// Phase 5: Integration
Task("Integration agent", "Deploy and validate", "workflow-manager")
```

---

### Pattern 2: Bug Fix Workflow

**Use Case**: Fix authentication token expiry bug

**Workflow**:
```
1. Light Specification (30 minutes)
   - Reproduce bug
   - Define expected behavior
   - Identify affected users

2. Skip Pseudocode (not needed for bug fix)

3. Light Architecture Review (15 minutes)
   - Verify component interactions
   - Check token flow

4. Refinement Focus (2-4 hours)
   - Write regression test (Red)
   - Fix the bug (Green)
   - Refactor if needed
   - Performance check

5. Quick Completion (30 minutes)
   - Run test suite
   - Update changelog
   - Deploy hotfix
```

**Agent Coordination**:
```javascript
Task("Debugger agent", "Reproduce and fix bug", "debugger")
Task("Tester agent", "Create regression test", "tester")
Task("Reviewer agent", "Review fix", "reviewer")
```

---

### Pattern 3: Architecture Refactoring

**Use Case**: Migrate monolith to microservices

**Workflow**:
```
1. Specification (1-2 days)
   - Current architecture analysis
   - Migration goals
   - Success criteria
   - Risk assessment

2. Pseudocode (1 day)
   - Service decomposition logic
   - Data migration algorithms
   - State synchronization

3. Architecture Emphasis (2-3 days)
   - Microservices design
   - API gateway setup
   - Service mesh planning
   - Data architecture

4. Iterative Refinement (2-4 weeks)
   - Strangler fig pattern
   - Service-by-service migration
   - Comprehensive testing
   - Performance monitoring

5. Gradual Completion (1 week)
   - Traffic cutover
   - Monitoring setup
   - Documentation
   - Team training
```

---

### Pattern 4: Parallel Component Development

**Use Case**: Build e-commerce platform (API + Frontend + Database)

**Workflow**:
```
// Phase 1-3: Synchronized planning
Specification → All components planned together
Pseudocode → Algorithms for all components
Architecture → Complete system design with interfaces

// Phase 4: Parallel implementation
[Parallel tasks]:
  Task("Backend team", "Build REST API", "coder")
  Task("Frontend team", "Build React UI", "coder")
  Task("Database team", "Schema + migrations", "coder")
  Task("Test team", "Integration tests", "tester")

// Phase 5: Integration
Integration testing → System validation → Deployment
```

**Key Success Factor**: Clear interface contracts from Architecture phase

---

### Pattern 5: Research-Driven Development

**Use Case**: Implement ML-based recommendation engine

**Workflow**:
```
1. Extended Specification (1 week)
   - Deep research on algorithms
   - Evaluate ML frameworks
   - Define success metrics
   - Gather training data

2. Prototype Pseudocode (3-5 days)
   - Multiple algorithm options
   - Complexity analysis
   - Performance predictions
   - Experimentation plan

3. Scalable Architecture (1 week)
   - ML pipeline design
   - Training infrastructure
   - Serving architecture
   - Monitoring strategy

4. Experimental Refinement (2-4 weeks)
   - A/B testing framework
   - Model training
   - Performance tuning
   - Iterative improvement

5. Production Completion (1 week)
   - Model deployment
   - Monitoring setup
   - Documentation
   - Team enablement
```

---

## Best Practices

### Phase-Specific Practices

**Specification**:
- ✅ Be specific and measurable
- ✅ Make everything testable
- ✅ Document edge cases
- ✅ Get early validation
- ❌ Don't use vague terms ("fast", "easy")
- ❌ Don't skip non-functional requirements

**Pseudocode**:
- ✅ Use language-agnostic syntax
- ✅ Always analyze complexity
- ✅ Identify design patterns
- ✅ Break complex logic into subroutines
- ❌ Don't use language-specific syntax
- ❌ Don't skip complexity analysis

**Architecture**:
- ✅ Design for failure
- ✅ Maintain loose coupling
- ✅ Build in observability
- ✅ Plan for scalability
- ❌ Don't over-engineer
- ❌ Don't ignore security

**Refinement**:
- ✅ Always write tests first
- ✅ Refactor continuously
- ✅ Monitor performance
- ✅ Keep changes small
- ❌ Don't skip tests
- ❌ Don't optimize prematurely

**Completion**:
- ✅ Run full test suite
- ✅ Complete documentation
- ✅ Validate in staging
- ✅ Monitor after deployment
- ❌ Don't skip integration tests
- ❌ Don't deploy without validation

---

### Quality Gates

**Gate 1: Specification → Pseudocode**
- [ ] All requirements documented
- [ ] Acceptance criteria clear
- [ ] Edge cases identified
- [ ] Stakeholders approved
- [ ] Success metrics defined

**Gate 2: Pseudocode → Architecture**
- [ ] Algorithms designed
- [ ] Complexity analyzed
- [ ] Patterns identified
- [ ] Optimization opportunities noted
- [ ] Logic validated

**Gate 3: Architecture → Refinement**
- [ ] System design complete
- [ ] Component interfaces defined
- [ ] Scalability planned
- [ ] Security reviewed
- [ ] Technology decisions made

**Gate 4: Refinement → Completion**
- [ ] Tests pass (>80% coverage)
- [ ] Code quality high
- [ ] Performance acceptable
- [ ] Error handling comprehensive
- [ ] Code reviewed

**Gate 5: Completion → Deployment**
- [ ] Integration tests pass
- [ ] Documentation complete
- [ ] Monitoring configured
- [ ] Security validated
- [ ] Deployment runbook ready

---

### Agent Coordination Best Practices

**Memory Usage**:
```bash
# Store phase outputs
memory_store "spec_complete_$(date +%s)" "Requirements documented"
memory_store "arch_decisions" "Microservices with event bus"

# Retrieve for next phase
memory_search "spec_complete" | tail -1
memory_search "arch_decisions"
```

**Hook Integration**:
```bash
# Pre-task hooks
npx claude-flow@alpha hooks pre-task --description "Implement auth"
npx claude-flow@alpha hooks session-restore --session-id "sparc-auth"

# Post-task hooks
npx claude-flow@alpha hooks post-task --task-id "auth-impl"
npx claude-flow@alpha hooks session-end --export-metrics true
```

**Parallel Execution**:
```javascript
// ALWAYS batch operations in single message
[Single Message]:
  Task("Agent 1", "Task 1 description", "type")
  Task("Agent 2", "Task 2 description", "type")
  Task("Agent 3", "Task 3 description", "type")

  TodoWrite { todos: [8-10 todos] }

  Write "file1.js"
  Write "file2.js"
  Write "file3.js"
```

---

## Integration Examples

### Example 1: Authentication System

**Objective**: Implement secure JWT authentication with OAuth2

**SPARC Execution**:

```javascript
// Complete SPARC workflow in single coordinated execution
mcp__claude-flow__task_orchestrate {
  task: "Implement JWT authentication with OAuth2 using SPARC methodology",
  strategy: "adaptive",
  priority: "high"
}

// Phase 1: Specification
Task("Spec agent", `
  Requirements:
  - JWT token authentication
  - OAuth2 (Google/GitHub)
  - Rate limiting
  - Session management
  - Security: OWASP Top 10
  - Performance: <200ms p95
`, "researcher")

// Phase 2: Pseudocode
Task("Pseudocode agent", `
  Design algorithms for:
  - Token generation/verification
  - Rate limiting (token bucket)
  - Session management
  - OAuth2 flow

  Analyze complexity and select data structures
`, "architect")

// Phase 3: Architecture
Task("Architecture agent", `
  Design:
  - Microservice architecture
  - API contracts (REST + gRPC)
  - Database schema (PostgreSQL)
  - Redis for sessions/cache
  - Infrastructure (Kubernetes)
`, "architect")

// Phase 4: Refinement (Parallel)
[Parallel tasks]:
  Task("Auth coder", "Implement auth service with TDD", "coder")
  Task("DB coder", "Create database schemas", "coder")
  Task("Test engineer", "Comprehensive test suite", "tester")
  Task("Security reviewer", "Security audit", "reviewer")

// Phase 5: Completion
Task("Integration agent", `
  - Integration testing
  - API documentation
  - Deployment to staging
  - Performance validation
  - Security scan
`, "workflow-manager")
```

**Result**: Production-ready authentication system in 3-5 days

---

### Example 2: Bug Fix with SPARC

**Objective**: Fix session expiry bug

```javascript
// Light SPARC for bug fix
Task("Bug fix agent", `
  1. Specification: Reproduce bug and define expected behavior
  2. Skip Pseudocode: Not needed for bug fix
  3. Light Architecture: Verify token flow
  4. Refinement Focus:
     - Write regression test
     - Fix bug
     - Refactor if needed
  5. Quick Completion:
     - Test suite
     - Deploy hotfix
`, "debugger")

Task("Test agent", "Create regression test", "tester")
Task("Review agent", "Review fix for edge cases", "reviewer")
```

**Result**: Bug fixed and deployed in 2-4 hours

---

### Example 3: Microservices Migration

**Objective**: Migrate monolith to microservices

```javascript
// Extended SPARC for large refactoring
mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 10 }

// Phase 1: Extended Specification (1-2 days)
Task("Research agent", `
  - Current architecture analysis
  - Service boundary identification
  - Migration strategy (Strangler Fig)
  - Risk assessment
  - Success criteria
`, "researcher")

// Phase 2-3: Architecture Emphasis (2-3 days)
Task("Lead architect", `
  - Service decomposition
  - API gateway design
  - Service mesh planning
  - Data migration strategy
  - Infrastructure architecture
`, "architect")

// Phase 4: Iterative Refinement (2-4 weeks)
[Weekly sprints]:
  Sprint 1: Extract user service
  Sprint 2: Extract order service
  Sprint 3: Extract payment service
  Sprint 4: Extract notification service

// Phase 5: Gradual Completion (1 week)
Task("Migration coordinator", `
  - Traffic cutover plan
  - Monitoring and alerting
  - Rollback procedures
  - Documentation
  - Team training
`, "workflow-manager")
```

**Result**: Successful migration with minimal downtime

---

## Quick Reference

### Command Cheatsheet

```bash
# List available modes
npx claude-flow sparc modes

# Execute specific mode
npx claude-flow sparc run <mode> "<task>"

# Complete TDD workflow
npx claude-flow sparc tdd "<feature>"

# Parallel execution
npx claude-flow sparc batch <modes> "<task>"

# Full pipeline
npx claude-flow sparc pipeline "<task>"

# Get mode details
npx claude-flow sparc info <mode>
```

### Mode Selection Guide

| Scenario | Recommended Mode(s) | Why |
|----------|-------------------|-----|
| New feature | SPARC Coordinator | Complete methodology |
| Bug fix | Debugger + Tester | Focus on fix + regression |
| Refactoring | Architect + Reviewer | Design + quality check |
| Documentation | Documenter | Specialized docs |
| Research | Researcher | Deep analysis |
| Code review | Reviewer | Quality assessment |
| Performance | Optimizer + Analyzer | Tune + profile |
| Testing | Tester + TDD | Comprehensive coverage |

### Integration Points

**GitHub**: Branch per phase, PRs at quality gates
**CI/CD**: Automated testing, deployment pipelines
**Monitoring**: Performance metrics, error tracking
**Documentation**: Auto-generated from code + manual guides

---

## Conclusion

SPARC methodology provides a systematic, quality-driven approach to software development. By following the five phases and utilizing specialized modes, teams can:

- **Deliver higher quality**: Through systematic planning and TDD
- **Reduce rework**: Clear requirements and design upfront
- **Scale effectively**: Parallel execution and agent coordination
- **Maintain velocity**: Automated workflows and quality gates
- **Ensure reliability**: Comprehensive testing and validation

**Key Success Factors**:
1. Don't skip phases (except for simple bug fixes)
2. Enforce quality gates
3. Use parallel execution for independent tasks
4. Leverage memory for cross-agent coordination
5. Document decisions and maintain traceability

**Next Steps**:
- Review the [CLAUDE.md](../CLAUDE.md) for project-specific setup
- Explore specific mode documentation in `.claude/commands/sparc/`
- Try the workflow patterns with your own projects
- Customize modes and workflows for your team's needs

---

*This guide is part of the Project B Blueprint SPARC implementation.*
*For issues or questions, please refer to the main project documentation.*
