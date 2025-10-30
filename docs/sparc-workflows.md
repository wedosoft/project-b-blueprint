# SPARC Workflow Patterns & Examples

## Table of Contents
1. [Complete Feature Development](#complete-feature-development)
2. [Bug Fix Workflow](#bug-fix-workflow)
3. [Architecture Refactoring](#architecture-refactoring)
4. [Parallel Component Development](#parallel-component-development)
5. [Research-Driven Development](#research-driven-development)
6. [Performance Optimization](#performance-optimization)
7. [Security Enhancement](#security-enhancement)
8. [Documentation Sprint](#documentation-sprint)

---

## Complete Feature Development

### Use Case: User Authentication System

**Objective**: Implement secure JWT authentication with OAuth2, rate limiting, and session management

**Timeline**: 3-5 days

### Phase Breakdown

#### Phase 1: Specification (Day 1, 2-4 hours)

**Agent**: Researcher Mode

**Activities**:
```yaml
requirements_gathering:
  functional:
    - JWT token generation and verification
    - OAuth2 integration (Google, GitHub)
    - Email/password authentication
    - Rate limiting (100 req/min per user)
    - Session management (24h expiry)
    - Two-factor authentication
    - Password reset flow

  non_functional:
    - Performance: <200ms p95 latency
    - Security: OWASP Top 10 compliance
    - Availability: 99.9% uptime
    - Scalability: 10,000 concurrent users

  constraints:
    - Use existing PostgreSQL database
    - Node.js 18+ runtime
    - Deploy to AWS EKS
    - Budget: $5,000/month infrastructure

acceptance_criteria:
  - scenario: "Successful login with valid credentials"
    given: "User has valid account"
    when: "User enters correct email/password"
    then: "User receives JWT token and redirect to dashboard"

  - scenario: "Rate limit exceeded"
    given: "User made 100 requests in 1 minute"
    when: "User attempts 101st request"
    then: "Return 429 Too Many Requests with retry-after header"
```

**Deliverables**:
- Requirements document with 15 functional requirements
- 8 non-functional requirements with metrics
- 20+ acceptance criteria in Gherkin format
- Edge cases documented (password reset, concurrent logins, expired tokens)
- Data model specification for User, Session, OAuth entities

**Quality Gate 1 Checklist**:
- [x] All requirements are testable and measurable
- [x] Acceptance criteria in Gherkin format
- [x] Edge cases documented
- [x] Performance metrics defined (<200ms p95)
- [x] Security requirements specified (OWASP Top 10)
- [x] Stakeholder approval obtained

---

#### Phase 2: Pseudocode (Day 1, 1-2 hours)

**Agent**: Pseudocode Architect Mode

**Activities**:
```
ALGORITHM: AuthenticateUser
INPUT: credentials {email: string, password: string}
OUTPUT: result {user: User, token: JWT} OR error

BEGIN
    // Input validation
    VALIDATE_EMAIL(credentials.email)
    VALIDATE_PASSWORD_FORMAT(credentials.password)

    // Rate limit check
    rateLimitKey ← CONCAT("login:", credentials.email)
    IF NOT CHECK_RATE_LIMIT(rateLimitKey, 5, 60) THEN
        RETURN ERROR("Rate limit exceeded")
    END IF

    // User lookup
    user ← DATABASE.findByEmail(credentials.email)
    IF user IS NULL THEN
        INCREMENT_RATE_LIMIT(rateLimitKey)
        RETURN ERROR("Invalid credentials")
    END IF

    // Password verification
    isValid ← BCRYPT.compare(credentials.password, user.passwordHash)
    IF NOT isValid THEN
        INCREMENT_RATE_LIMIT(rateLimitKey)
        AUDIT_LOG("failed_login", user.id, credentials.email)
        RETURN ERROR("Invalid credentials")
    END IF

    // Generate tokens
    accessToken ← JWT.sign({
        userId: user.id,
        email: user.email,
        roles: user.roles
    }, SECRET, {expiresIn: "15m"})

    refreshToken ← JWT.sign({
        userId: user.id,
        tokenType: "refresh"
    }, REFRESH_SECRET, {expiresIn: "7d"})

    // Create session
    session ← DATABASE.createSession({
        userId: user.id,
        tokenHash: HASH(accessToken),
        expiresAt: NOW() + 15_MINUTES,
        ipAddress: REQUEST.ip,
        userAgent: REQUEST.userAgent
    })

    // Store in cache
    CACHE.set(CONCAT("session:", accessToken), session, 15_MINUTES)

    AUDIT_LOG("successful_login", user.id, credentials.email)
    RESET_RATE_LIMIT(rateLimitKey)

    RETURN {user: user, accessToken: accessToken, refreshToken: refreshToken}
END

COMPLEXITY ANALYSIS:
  Time Complexity:
    - Email validation: O(1)
    - Rate limit check: O(1) - Redis lookup
    - Database user lookup: O(log n) - indexed email
    - Password verification: O(1) - fixed bcrypt rounds
    - Token generation: O(1)
    - Cache operations: O(1)
    - Total: O(log n) dominated by DB lookup

  Space Complexity:
    - Input storage: O(1)
    - User object: O(1)
    - Session data: O(1)
    - Total: O(1)

DATA STRUCTURE: Rate Limiting (Token Bucket)
  Structure: Redis Hash
    Key: "ratelimit:{identifier}"
    Fields:
      - tokens: current available tokens
      - lastRefill: timestamp of last refill
      - capacity: maximum tokens (100)
      - refillRate: tokens per second (1.67)

  Operations:
    - checkLimit(): O(1) - Redis HGETALL
    - consumeToken(): O(1) - Redis HINCRBY
    - refillTokens(): O(1) - Redis HSET

PATTERN: Strategy Pattern for Authentication
  Interface: AuthStrategy
    - authenticate(credentials): Promise<AuthResult>

  Implementations:
    - EmailPasswordStrategy
    - OAuthGoogleStrategy
    - OAuthGitHubStrategy
    - TwoFactorStrategy
```

**Deliverables**:
- Complete pseudocode for 8 major functions
- Data structure specifications (Token Bucket, Session Cache)
- Complexity analysis for all algorithms
- Design patterns identified (Strategy, Observer, Factory)
- Optimization notes (Redis caching, connection pooling)

**Quality Gate 2 Checklist**:
- [x] All algorithms designed with clear logic
- [x] Time/space complexity analyzed
- [x] Data structures selected with justification
- [x] Design patterns identified
- [x] Edge cases handled in pseudocode

---

#### Phase 3: Architecture (Day 2, 2-3 hours)

**Agent**: System Architect Mode

**Activities**:

**High-Level Architecture**:
```
┌──────────────┐
│   Clients    │
│ Web/Mobile   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ API Gateway  │
│ (Kong/Nginx) │
│ - Rate Limit │
│ - TLS Term   │
└──────┬───────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│    Auth     │   │    User     │   │  Notification│
│  Service    │◄──┤  Service    │◄──┤   Service   │
│ (NestJS)    │   │  (NestJS)   │   │   (Node)    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────────────────────────────────────┐
│           Shared Infrastructure              │
│  ┌──────────┐ ┌─────────┐ ┌──────────┐     │
│  │PostgreSQL│ │  Redis  │ │ RabbitMQ │     │
│  └──────────┘ └─────────┘ └──────────┘     │
│  ┌──────────┐ ┌─────────┐                  │
│  │Prometheus│ │ELK Stack│                  │
│  └──────────┘ └─────────┘                  │
└──────────────────────────────────────────────┘
```

**Component Specification**:
```yaml
auth_service:
  name: "Authentication Service"
  type: "Microservice"
  technology:
    language: "TypeScript"
    framework: "NestJS 10"
    runtime: "Node.js 18"
    orm: "Prisma"

  responsibilities:
    - "User authentication (JWT, OAuth2)"
    - "Token management (generate, verify, refresh)"
    - "Session handling"
    - "Rate limiting"
    - "Security audit logging"

  api_endpoints:
    rest:
      - POST /api/v1/auth/login
      - POST /api/v1/auth/logout
      - POST /api/v1/auth/refresh
      - GET /api/v1/auth/verify
      - POST /api/v1/auth/oauth/{provider}
      - POST /api/v1/auth/reset-password

    grpc:
      - service AuthService
        - rpc VerifyToken(VerifyTokenRequest) returns (User)
        - rpc InvalidateSession(SessionId) returns (Status)
        - rpc GetUserPermissions(UserId) returns (PermissionList)

  events:
    publishes:
      - user.logged_in: {userId, timestamp, ipAddress}
      - user.logged_out: {userId, timestamp}
      - session.expired: {sessionId, userId}
      - auth.rate_limit_exceeded: {userId, endpoint}

    subscribes:
      - user.deleted: {userId} → invalidate all sessions
      - user.password_changed: {userId} → invalidate sessions
      - user.suspended: {userId} → block authentication

  dependencies:
    internal:
      - user_service (gRPC): User data operations
      - notification_service (events): Email notifications

    external:
      - postgresql: User/session persistence
      - redis: Session cache, rate limiting
      - rabbitmq: Event bus
      - oauth_providers: Google, GitHub APIs

  scaling:
    horizontal: true
    instances:
      min: 2
      max: 10
      target_cpu: 70%
      target_memory: 80%

  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"

  health_checks:
    liveness: /health (30s interval)
    readiness: /ready (5s interval)
```

**Database Schema**:
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_users_email (email),
    INDEX idx_users_status (status),
    INDEX idx_users_created_at (created_at)
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_token_hash (token_hash),
    INDEX idx_sessions_expires_at (expires_at)
);

-- OAuth connections
CREATE TABLE oauth_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(provider, provider_user_id),
    INDEX idx_oauth_user_id (user_id)
);

-- Audit logs (partitioned by month)
CREATE TABLE audit_logs (
    id BIGSERIAL,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_user_id (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created_at (created_at)
) PARTITION BY RANGE (created_at);
```

**Infrastructure (Kubernetes)**:
```yaml
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
      - name: auth-service
        image: auth-service:v1.0.0
        ports:
        - containerPort: 3000
          name: http
        - containerPort: 50051
          name: grpc
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5

# HorizontalPodAutoscaler
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Deliverables**:
- Complete system architecture diagram
- 3 microservice specifications
- Database schema with indexes
- API contract (REST + gRPC)
- Infrastructure manifests (Kubernetes)
- Security architecture (JWT, OAuth2, encryption)
- Scalability plan (HPA, caching strategy)

**Quality Gate 3 Checklist**:
- [x] System design complete with diagrams
- [x] All component interfaces defined
- [x] Database schema optimized
- [x] API contracts specified (OpenAPI/gRPC)
- [x] Scalability strategy documented
- [x] Security reviewed (encryption, auth, audit)
- [x] Infrastructure defined (K8s manifests)

---

#### Phase 4: Refinement (Days 2-4, 8-16 hours)

**Agents**: Multiple parallel agents for concurrent development

**Parallel Tasks**:
```javascript
[Single Message - Parallel Execution]:
  // Backend implementation
  Task("Auth Coder", `
    Implement auth-service using TDD:
    1. Setup NestJS project with Prisma ORM
    2. RED: Write failing tests for login endpoint
    3. GREEN: Implement minimum code to pass
    4. REFACTOR: Extract to services, improve quality
    5. Repeat for all 6 endpoints
    Coverage target: >85%
  `, "coder")

  // Database implementation
  Task("Database Coder", `
    1. Create Prisma schema from architecture
    2. Generate and test migrations
    3. Seed development data
    4. Create database indexes
    5. Setup connection pooling
  `, "coder")

  // Testing implementation
  Task("Test Engineer", `
    Create comprehensive test suite:
    1. Unit tests for all services (>90% coverage)
    2. Integration tests for API endpoints
    3. E2E tests for auth flows
    4. Performance tests (load testing)
    5. Security tests (OWASP Top 10)
  `, "tester")

  // Security review
  Task("Security Reviewer", `
    Security audit:
    1. Review JWT implementation
    2. Check password hashing (bcrypt rounds)
    3. Verify rate limiting
    4. Test SQL injection protection
    5. Validate session management
    6. OAuth2 flow security
  `, "reviewer")

  // All todos in single call
  TodoWrite { todos: [
    {id: "1", content: "Setup NestJS + Prisma project", status: "in_progress"},
    {id: "2", content: "Implement JWT generation/verification", status: "pending"},
    {id: "3", content: "Build login endpoint with TDD", status: "pending"},
    {id: "4", content: "Implement OAuth2 integration", status: "pending"},
    {id: "5", content: "Add rate limiting middleware", status: "pending"},
    {id: "6", content: "Create database migrations", status: "pending"},
    {id: "7", content: "Write unit tests (>85% coverage)", status: "pending"},
    {id: "8", content: "Create integration tests", status: "pending"},
    {id: "9", content: "Performance testing", status: "pending"},
    {id: "10", content: "Security audit", status: "pending"}
  ]}
```

**TDD Cycle Example - Login Endpoint**:

**RED Phase** (Write failing test):
```typescript
describe('AuthController - /auth/login', () => {
  let app: INestApplication;
  let prisma: PrismaService;

  beforeAll(async () => {
    const module = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = module.createNestApplication();
    await app.init();
    prisma = app.get(PrismaService);
  });

  it('should return JWT token for valid credentials', async () => {
    // Arrange: Create test user
    const user = await prisma.user.create({
      data: {
        email: 'test@example.com',
        passwordHash: await bcrypt.hash('Password123!', 10),
      },
    });

    // Act: Login request
    const response = await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send({
        email: 'test@example.com',
        password: 'Password123!',
      });

    // Assert
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('accessToken');
    expect(response.body).toHaveProperty('refreshToken');
    expect(response.body.user).toMatchObject({
      id: user.id,
      email: user.email,
    });

    // Verify JWT
    const decoded = jwt.verify(response.body.accessToken, process.env.JWT_SECRET);
    expect(decoded).toHaveProperty('userId', user.id);
  });

  it('should rate limit after 5 failed attempts', async () => {
    const credentials = {
      email: 'test@example.com',
      password: 'WrongPassword',
    };

    // Make 5 failed attempts
    for (let i = 0; i < 5; i++) {
      await request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send(credentials);
    }

    // 6th attempt should be rate limited
    const response = await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send(credentials);

    expect(response.status).toBe(429);
    expect(response.body.message).toContain('Rate limit exceeded');
    expect(response.headers).toHaveProperty('retry-after');
  });
});
```

**GREEN Phase** (Implement to pass):
```typescript
@Controller('api/v1/auth')
export class AuthController {
  constructor(
    private authService: AuthService,
    private rateLimitService: RateLimitService,
  ) {}

  @Post('login')
  async login(@Body() loginDto: LoginDto, @Req() req: Request) {
    // Rate limit check
    const rateLimitKey = `login:${loginDto.email}`;
    const isAllowed = await this.rateLimitService.checkLimit(
      rateLimitKey,
      5,  // Max 5 attempts
      60, // Per 60 seconds
    );

    if (!isAllowed) {
      throw new TooManyRequestsException('Rate limit exceeded. Try again in 1 minute.');
    }

    try {
      const result = await this.authService.login(loginDto, {
        ipAddress: req.ip,
        userAgent: req.headers['user-agent'],
      });

      return result;
    } catch (error) {
      // Increment rate limit on failure
      await this.rateLimitService.incrementLimit(rateLimitKey);
      throw error;
    }
  }
}

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwtService: JwtService,
    private eventEmitter: EventEmitter2,
  ) {}

  async login(loginDto: LoginDto, context: LoginContext): Promise<LoginResult> {
    // Find user
    const user = await this.prisma.user.findUnique({
      where: { email: loginDto.email },
    });

    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(
      loginDto.password,
      user.passwordHash,
    );

    if (!isValidPassword) {
      this.auditLog('failed_login', user.id, context);
      throw new UnauthorizedException('Invalid credentials');
    }

    // Generate tokens
    const tokens = await this.generateTokens(user);

    // Create session
    await this.createSession(user.id, tokens.accessToken, context);

    // Emit event
    this.eventEmitter.emit('user.logged_in', {
      userId: user.id,
      timestamp: new Date(),
      ipAddress: context.ipAddress,
    });

    return {
      user: this.sanitizeUser(user),
      ...tokens,
    };
  }

  private async generateTokens(user: User) {
    const accessToken = this.jwtService.sign(
      { userId: user.id, email: user.email },
      { expiresIn: '15m' },
    );

    const refreshToken = this.jwtService.sign(
      { userId: user.id, tokenType: 'refresh' },
      { secret: process.env.REFRESH_SECRET, expiresIn: '7d' },
    );

    return { accessToken, refreshToken };
  }
}
```

**REFACTOR Phase** (Improve quality):
```typescript
// Extract validation to decorator
@Post('login')
@UseGuards(RateLimitGuard)
@UsePipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }))
async login(@Body() loginDto: LoginDto, @Req() req: Request) {
  return this.authService.login(loginDto, this.extractContext(req));
}

// Extract context creation
private extractContext(req: Request): LoginContext {
  return {
    ipAddress: req.ip,
    userAgent: req.headers['user-agent'],
    timestamp: new Date(),
  };
}

// Improve service with better separation
@Injectable()
export class AuthService {
  constructor(
    private userRepo: UserRepository,
    private sessionRepo: SessionRepository,
    private tokenService: TokenService,
    private auditService: AuditService,
    private eventBus: EventEmitter2,
  ) {}

  async login(dto: LoginDto, context: LoginContext): Promise<LoginResult> {
    const user = await this.authenticateUser(dto);
    const tokens = await this.tokenService.generate(user);
    const session = await this.sessionRepo.create(user.id, tokens, context);

    this.auditService.log('login_success', user.id, context);
    this.eventBus.emit('user.logged_in', { userId: user.id, context });

    return {
      user: this.userRepo.sanitize(user),
      tokens,
      session: { id: session.id, expiresAt: session.expiresAt },
    };
  }

  private async authenticateUser(dto: LoginDto): Promise<User> {
    const user = await this.userRepo.findByEmail(dto.email);

    if (!user || !(await this.verifyPassword(dto.password, user.passwordHash))) {
      throw new UnauthorizedException('Invalid credentials');
    }

    if (user.status !== 'active') {
      throw new ForbiddenException('Account is not active');
    }

    return user;
  }
}
```

**Performance Optimization**:
```typescript
// Add caching layer
@Injectable()
export class CachedSessionService {
  constructor(
    private sessionRepo: SessionRepository,
    private cacheService: RedisService,
  ) {}

  async findByToken(token: string): Promise<Session | null> {
    const cacheKey = `session:${token}`;

    // Check cache first
    const cached = await this.cacheService.get(cacheKey);
    if (cached) return JSON.parse(cached);

    // Fallback to database
    const session = await this.sessionRepo.findByToken(token);
    if (session) {
      await this.cacheService.set(
        cacheKey,
        JSON.stringify(session),
        15 * 60, // 15 minutes
      );
    }

    return session;
  }
}

// Database query optimization with connection pooling
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")

  // Connection pooling
  connection_limit = 100
  pool_timeout = 30
}
```

**Deliverables**:
- Fully implemented auth service (3,000+ lines of code)
- Test suite with >85% coverage
  - 120+ unit tests
  - 40+ integration tests
  - 15+ E2E tests
- Performance optimizations (caching, query optimization)
- Error handling with custom exceptions
- Security features (rate limiting, audit logging)
- Code quality score: A+ (SonarQube)

**Quality Gate 4 Checklist**:
- [x] All tests passing (unit, integration, E2E)
- [x] Code coverage >85%
- [x] Performance: <200ms p95 latency achieved
- [x] No critical security vulnerabilities
- [x] Code quality: A+ rating
- [x] Error handling comprehensive
- [x] Code reviewed and approved

---

#### Phase 5: Completion (Day 5, 2-4 hours)

**Agent**: Workflow Manager Mode

**Activities**:

**Integration Testing**:
```typescript
describe('Auth System Integration', () => {
  it('should complete full authentication flow', async () => {
    // 1. Register user
    const registerRes = await request(app)
      .post('/api/v1/users/register')
      .send({ email: 'user@test.com', password: 'Pass123!' });

    expect(registerRes.status).toBe(201);

    // 2. Login
    const loginRes = await request(app)
      .post('/api/v1/auth/login')
      .send({ email: 'user@test.com', password: 'Pass123!' });

    expect(loginRes.status).toBe(200);
    const { accessToken, refreshToken } = loginRes.body;

    // 3. Access protected resource
    const protectedRes = await request(app)
      .get('/api/v1/users/profile')
      .set('Authorization', `Bearer ${accessToken}`);

    expect(protectedRes.status).toBe(200);

    // 4. Refresh token
    const refreshRes = await request(app)
      .post('/api/v1/auth/refresh')
      .send({ refreshToken });

    expect(refreshRes.status).toBe(200);
    expect(refreshRes.body.accessToken).toBeDefined();

    // 5. Logout
    const logoutRes = await request(app)
      .post('/api/v1/auth/logout')
      .set('Authorization', `Bearer ${accessToken}`);

    expect(logoutRes.status).toBe(200);

    // 6. Verify token invalidated
    const invalidRes = await request(app)
      .get('/api/v1/users/profile')
      .set('Authorization', `Bearer ${accessToken}`);

    expect(invalidRes.status).toBe(401);
  });
});
```

**API Documentation** (OpenAPI):
```yaml
openapi: 3.0.3
info:
  title: Authentication API
  version: 1.0.0
  description: Secure JWT-based authentication with OAuth2 support

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

paths:
  /auth/login:
    post:
      summary: User login
      tags: [Authentication]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                  example: user@example.com
                password:
                  type: string
                  minLength: 8
                  example: SecurePass123!
      responses:
        200:
          description: Successful authentication
          content:
            application/json:
              schema:
                type: object
                properties:
                  accessToken:
                    type: string
                    description: JWT access token (15min expiry)
                  refreshToken:
                    type: string
                    description: Refresh token (7 days expiry)
                  user:
                    $ref: '#/components/schemas/User'
        401:
          description: Invalid credentials
        429:
          description: Rate limit exceeded
```

**Deployment**:
```bash
# Build Docker image
docker build -t auth-service:v1.0.0 .

# Push to registry
docker push registry.example.com/auth-service:v1.0.0

# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

# Run database migrations
kubectl exec -it auth-service-pod -- npm run migrate:prod

# Verify deployment
kubectl rollout status deployment/auth-service
kubectl get pods -l app=auth-service
```

**Monitoring Setup**:
```yaml
# Prometheus metrics
apiVersion: v1
kind: Service
metadata:
  name: auth-service-metrics
  labels:
    app: auth-service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "3000"
    prometheus.io/path: "/metrics"

# Grafana dashboard
dashboards:
  - name: "Auth Service Performance"
    panels:
      - title: "Request Rate"
        query: 'rate(http_requests_total{service="auth"}[5m])'
      - title: "Error Rate"
        query: 'rate(http_errors_total{service="auth"}[5m])'
      - title: "Response Time (p95)"
        query: 'histogram_quantile(0.95, http_request_duration_seconds{service="auth"})'
      - title: "Active Sessions"
        query: 'auth_active_sessions_total'
```

**Deliverables**:
- Comprehensive integration test suite
- OpenAPI documentation (Swagger UI)
- Deployment runbooks
- Monitoring dashboards (Prometheus + Grafana)
- Performance validation report
- Security audit report
- Production readiness checklist

**Quality Gate 5 Checklist**:
- [x] All integration tests passing
- [x] API documentation complete (OpenAPI 3.0)
- [x] Successfully deployed to staging
- [x] Performance validated: <200ms p95 ✓
- [x] Security audit passed (no critical issues)
- [x] Monitoring dashboards configured
- [x] Runbooks documented
- [x] Production readiness: APPROVED

---

### Results

**Timeline**: 5 days (vs 10-15 days without SPARC)
**Quality**: 85% code coverage, 0 critical bugs in production
**Performance**: 150ms p95 (25% better than requirement)
**Scalability**: Successfully handling 15,000 concurrent users
**Maintainability**: A+ code quality rating

---

## Bug Fix Workflow

### Use Case: Session Token Expiry Bug

**Objective**: Fix bug where tokens expire prematurely

**Timeline**: 2-4 hours

### Lightweight SPARC Approach

#### Phase 1: Light Specification (30 minutes)

**Reproduce Bug**:
```
Steps to reproduce:
1. User logs in successfully
2. User navigates away for 10 minutes
3. User returns and tries to use app
4. Token is expired (should still be valid for 15 minutes)

Expected: Token valid for 15 minutes
Actual: Token expires after ~8 minutes
Impact: 200+ users affected, support tickets increasing
```

**Define Fix**:
- Token expiry time not correctly set
- Need to verify JWT expiration claim
- Add test to prevent regression

#### Phase 2: Skip Pseudocode
(Not needed for straightforward bug fix)

#### Phase 3: Light Architecture Review (15 minutes)

**Verify Components**:
```
Token Flow:
  AuthService.generateToken()
    ↓
  JWT.sign({ payload }, secret, { expiresIn: '15m' })
    ↓
  Token sent to client
    ↓
  Client stores in localStorage
    ↓
  AuthGuard.canActivate() verifies token
    ↓
  JWT.verify() checks expiration
```

**Root Cause**: `expiresIn` value is '15' instead of '15m', resulting in 15 seconds

#### Phase 4: Refinement (2-3 hours)

**RED - Write Regression Test**:
```typescript
it('should generate token with 15 minute expiry', async () => {
  const user = { id: 'user-123', email: 'test@example.com' };

  const token = await authService.generateAccessToken(user);
  const decoded = jwt.decode(token) as any;

  // Verify expiration is ~15 minutes from now
  const expiresAt = new Date(decoded.exp * 1000);
  const now = new Date();
  const diffMinutes = (expiresAt.getTime() - now.getTime()) / 1000 / 60;

  expect(diffMinutes).toBeGreaterThan(14);
  expect(diffMinutes).toBeLessThan(16);
});
```

**GREEN - Fix Bug**:
```typescript
// Before (WRONG)
this.jwtService.sign(payload, { expiresIn: '15' }) // 15 seconds!

// After (CORRECT)
this.jwtService.sign(payload, { expiresIn: '15m' }) // 15 minutes
```

**REFACTOR - Improve**:
```typescript
// Extract to constant
const TOKEN_EXPIRY = {
  ACCESS: '15m',
  REFRESH: '7d',
} as const;

// Use constant
this.jwtService.sign(payload, { expiresIn: TOKEN_EXPIRY.ACCESS })
```

#### Phase 5: Quick Completion (30 minutes)

- Run full test suite ✓
- Update changelog
- Deploy hotfix to production
- Monitor for 1 hour
- Update documentation

**Result**: Bug fixed and deployed in 4 hours, 0 regressions

---

(Continues with remaining workflow patterns...)

*This document provides detailed workflow examples for all SPARC patterns. Each pattern includes timeline, phase breakdown, agent coordination, code examples, and results.*
