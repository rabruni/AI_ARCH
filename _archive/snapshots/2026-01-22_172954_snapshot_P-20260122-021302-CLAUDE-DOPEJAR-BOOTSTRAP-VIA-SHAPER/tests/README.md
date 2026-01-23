# /tests

Test suites for the project.

## What Belongs Here

- Unit tests
- Integration tests
- End-to-end tests
- Test fixtures and utilities
- Conftest files

## What Does NOT Belong Here

- Application source code (belongs in `/src`)
- Test data that contains secrets or PII
- Large binary test fixtures (should be downloaded or generated)

## Structure Convention

Tests should mirror the `/src` directory structure:

```
/src/module/component.py  ->  /tests/module/test_component.py
```
