# AGENTS.md

## Project overview

Phoenix API v1 is a Pyramid application using SQLAlchemy, Alembic, PostgreSQL,
and pytest. Application code lives in `phoenixRest/`, migrations live in
`alembic/versions/`, and tests live in `phoenixRest/tests/`.

## Working conventions

- Preserve unrelated user changes in the worktree.
- Use `rg` for file and text searches.
- Make focused changes that follow the existing module structure and style.
- Do not rewrite migration history unless the task explicitly requests it.
- Keep production migrations free of test-only seed data. Test users and other
  test-only model instances belong in pytest fixtures in
  `phoenixRest/tests/conftest.py`.
- Prefer explicit fixture dependencies. A test should request the users, crews,
  teams, events, or other records it actually uses instead of relying on
  database state created elsewhere.
- Do not hardcode shared fixture-user emails in tests. Read identity fields from
  the corresponding user fixture.

## Testing

- The only supported way to run tests is `./test.sh` with `testing/` as the
  working directory (equivalently, `cd testing && ./test.sh`).
- Do not invoke `pytest`, `python -m pytest`, or an individual test module
  directly, including for collection-only checks.
- `testing/test.sh` uses Docker Compose and supplies the database and required
  service environment.
- If the Docker-based test command cannot run, report the blocker instead of
  substituting another test command.

## Database changes

- Keep Alembic upgrade and downgrade paths structurally valid.
- When removing seeded records, also remove dependent seed records and obsolete
  UUID variables while retaining required table and constraint creation.
- Validate migration-dependent tests against a database freshly created by the
  supported test workflow.

## Completion checks

- Search for stale references to removed seed names and identifiers.
- Check that every shared test record is introduced through an explicit fixture.
- Run `testing/test.sh` when verification is required and Docker is available.
- Summarize changed behavior and any verification blockers in the handoff.
