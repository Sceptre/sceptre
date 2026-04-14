---
inclusion: manual
---

# E2E Testing Skill

Activate this skill when writing end-to-end or integration tests for the RAG pipeline and connectors.

## Test Structure

### Fixture Pattern
Encapsulate setup in reusable pytest fixtures:

```python
import pytest

@pytest.fixture
def opensearch_client():
    client = get_test_opensearch_client()
    yield client
    # teardown: clean up test index
    client.indices.delete(index="test-*", ignore_unavailable=True)

@pytest.fixture
def seeded_index(opensearch_client):
    index_test_documents(opensearch_client)
    return opensearch_client
```

### Test Pattern

```python
def test_rag_query_returns_cited_answer(seeded_index, mock_bedrock):
    # Arrange
    query = "What is the SOP for data access requests?"

    # Act
    result = run_rag_query(query, user_id="U123", opensearch_client=seeded_index)

    # Assert
    assert result.answer is not None
    assert len(result.sources) > 0
    assert result.confidence in ("High", "Medium", "Low")
```

## Best Practices

- Use pytest fixtures for test setup/teardown
- Use `pytest.mark.parametrize` for multiple input scenarios
- Test user-observable behavior, not internal implementation
- Keep tests independent — each test starts from a clean state
- Use `moto` for mocking AWS services (S3, SQS, Secrets Manager)
- Use `unittest.mock.patch` or `pytest-mock` for Bedrock/OpenSearch

## What to Test E2E

- Full query flow: SQS message → identity lookup → retrieval → generation → Slack response
- Connector ingestion: fetch → chunk → embed → index
- Rate limiting behavior under concurrent load
- Authorization filtering (restricted content not returned to unauthorized users)
- Feedback flow: interaction payload → storage

## What NOT to Test E2E

- Individual utility functions (use unit tests)
- CDK construct synthesis (use CDK assertions)
- Every possible input combination (use parametrize in unit tests)

## Debugging Failed Tests

1. Check pytest output with `-v` and `--tb=long`
2. Look at mock call args to verify correct API calls
3. Run the specific test in isolation: `pytest -k "test_name" -s`
4. Add `breakpoint()` to stop at a specific point
5. Check fixture teardown for leftover state
