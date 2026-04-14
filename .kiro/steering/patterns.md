---
inclusion: always
---

# Design Patterns & Principles

## SOLID Principles

- **Single Responsibility** — Each module/function does one thing well
- **Open/Closed** — Extend behavior without modifying existing code
- **Liskov Substitution** — Subtypes must be substitutable for their base types
- **Interface Segregation** — Prefer small, focused interfaces
- **Dependency Inversion** — Depend on abstractions, not concretions

## Preferred Patterns

- **Composition over inheritance** — Compose behaviors from small pieces
- **Early returns** — Reduce nesting, handle edge cases first
- **Strategy pattern** — Swap algorithms without changing callers
- **Repository pattern** — Abstract data access behind a clean interface
- **Middleware pattern** — Chain cross-cutting concerns (auth, logging, validation)

## Architecture Guidelines

- Separate concerns: UI, business logic, data access
- Keep business logic framework-agnostic where possible
- Use dependency injection for testability
- Prefer pure functions — same input always produces same output
- Minimize shared mutable state

## When Starting New Features

1. Define the interface/contract first
2. Write tests against the interface
3. Implement the simplest version that works
4. Refactor toward clean patterns
5. Document non-obvious decisions with comments explaining "why"
