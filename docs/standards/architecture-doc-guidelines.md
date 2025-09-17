# Architecture Document Guidelines

## Document Structure

### 1. Executive Summary (200-300 words)
- Problem statement and business context
- Proposed solution overview
- Key architectural decisions
- Expected outcomes and benefits

### 2. System Context
- Current state architecture
- Integration points and dependencies
- Data flow patterns
- Security boundaries

### 3. Technical Design

#### 3.1 Component Architecture
- Component diagram with clear boundaries
- Responsibilities and interfaces
- Communication patterns (sync/async)
- Data ownership model

#### 3.2 Data Architecture
- Entity relationships
- Storage patterns and partitioning
- Consistency requirements
- Migration strategies

#### 3.3 Code Organization Standards

**File Size Guidelines**:
- **Target Size**: 500 lines per file
- **Acceptable Range**: 300-700 lines
- **Rationale**: Balances code cohesion with cognitive complexity
- **Split Criteria**: Logical boundaries over arbitrary line counts

**File Organization Strategy**:
```
# Good: Domain-driven organization
domain/
├── core_operations.py     # ~500 lines: Primary domain logic
├── optimization.py        # ~400 lines: Performance enhancements
├── validation.py          # ~300 lines: Input/output validation
└── utilities.py           # ~250 lines: Helper functions

# Bad: Size-driven splits
domain/
├── operations_1.py        # 350 lines: Arbitrary split
├── operations_2.py        # 350 lines: No logical boundary
└── monolith.py           # 1500 lines: Too complex
```

**Split Decision Framework**:
1. **Domain Boundaries**: Different business concerns
2. **Abstraction Levels**: Core logic vs utilities
3. **Change Frequency**: Stable vs evolving code
4. **Testing Scope**: Unit vs integration concerns
5. **Dependency Patterns**: High vs low coupling

**Quality Metrics**:
- Files >700 lines require architectural review
- Files <200 lines should justify separate existence
- Average file size target: 400-500 lines
- No single file should exceed 1000 lines

#### 3.4 Function Signatures
```python
# Example format for all critical functions
def function_name(
    param1: Type,
    param2: Type,
    *,  # Force keyword-only args for clarity
    optional_param: Optional[Type] = None
) -> ReturnType:
    """
    Brief description of function purpose.

    Args:
        param1: What this parameter represents
        param2: What this parameter represents
        optional_param: When and why to use this

    Returns:
        Description of return value and structure

    Raises:
        ExceptionType: When this exception occurs
    """
```

### 4. Architectural Principles Compliance

#### 4.1 Set Theory Operations
- Document all filtering operations as pure set theory
- Provide mathematical notation for complex operations
- Example: `result = (A ∩ B) ∪ (C - D)`

#### 4.2 Function-Based Architecture
- NO classes except for approved types (Pydantic, SQLAlchemy)
- All business logic as pure functions
- State passed explicitly, never hidden

#### 4.3 JavaScript Restrictions
- Document any required JavaScript (should be minimal)
- Justify why HTMX cannot achieve the requirement
- Limit to approved patterns (WASM loading, DOM properties)

### 5. Performance Considerations
- Scalability analysis (horizontal scaling capability)
- Bottleneck identification
- Caching strategies using approved singleton patterns
- Resource utilization estimates

### 6. Security Architecture
- Authentication and authorization patterns
- Data isolation mechanisms
- Secret management approach
- Audit logging requirements

### 7. Error Handling
- Error classification and handling strategies
- Rollback procedures
- Recovery mechanisms
- User experience during failures

### 8. Testing Strategy
- Unit test requirements (100% coverage target)
- Integration test patterns
- Performance test criteria
- Migration test procedures

### 9. Deployment Architecture
- Environment configurations
- Rollout strategy
- Rollback procedures
- Monitoring and alerting

### 10. Risk Assessment
- Technical risks and mitigations
- Operational risks
- Security risks
- Business continuity plans

### 11. Decision Log
- Key decisions with rationale
- Alternatives considered
- Trade-offs accepted
- Future considerations

### 12. Appendices
- Glossary of terms
- Reference documentation links
- Detailed calculations
- Supporting research

## Quality Checklist
- [ ] All functions have complete signatures
- [ ] Set theory operations documented mathematically
- [ ] No unauthorized classes or JavaScript
- [ ] Performance implications analyzed
- [ ] Security boundaries clearly defined
- [ ] Error scenarios comprehensively covered
- [ ] Testing approach specified
- [ ] Rollback procedures documented
- [ ] Risks identified and mitigated
- [ ] Decisions justified with rationale
