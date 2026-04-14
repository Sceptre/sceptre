---
inclusion: auto
description: API design conventions for endpoints, responses, and pagination
---

# API Conventions

- All endpoints return `{ data, error, meta }`
- Plural nouns, nested resources: `/api/products/:id/reviews`
- No verbs in URLs, filter via query params
- Paginate with `?page=1&limit=20`, default 20 items
- 400s include field-level details, 500s never expose stack traces
