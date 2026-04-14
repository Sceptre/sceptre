---
inclusion: always
---

# Performance Guidelines

## Backend (Python)

- Use database indexes for frequently queried columns
- Implement pagination for list endpoints (never return unbounded results)
- Cache expensive computations and repeated queries
- Use connection pooling for database connections (SQLAlchemy pool, psycopg2 pool)
- Set appropriate timeouts on external API calls
- Use async I/O (`asyncio`, `aiohttp`, `httpx`) for concurrent external calls
- Use generators/iterators for large datasets instead of loading everything into memory
- Profile with `cProfile`, `line_profiler`, or `py-spy` before optimizing

## AWS-Specific

- Use VPC endpoints to reduce NAT gateway costs and latency
- Right-size ECS Fargate tasks (CPU/memory)
- Use SQS batch operations where possible
- Monitor Bedrock invocation latency and implement caching for repeated queries
- Use OpenSearch bulk indexing for ingestion

## General

- Measure before optimizing — don't guess at bottlenecks
- Profile with real data, not toy examples
- Set performance budgets (response time targets: median <8s, p95 <15s)
- Monitor performance in production, not just development

## Anti-Patterns to Avoid

- N+1 queries (fetch related data in batch, not per-item)
- Synchronous blocking I/O in async handlers
- Unbounded in-memory caches (use LRU with `functools.lru_cache` or `cachetools`)
- Loading entire datasets when only a subset is needed
- Creating new database connections per request instead of pooling
