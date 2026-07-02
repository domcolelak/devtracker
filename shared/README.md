# devtracker-shared

Shared enums and Pydantic models used by more than one DevTracker service, so
that things like task status values cannot silently drift apart between
`api-fastapi` and `reports-flask`.

Installed as an editable local package inside each service's Docker image:

```
pip install -e /shared
```

Keep this package free of framework-specific code (no Django, no FastAPI, no
Flask imports) so any service can depend on it without pulling in unrelated
dependencies.
