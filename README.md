# cognee-dokploy

Cognee self-hosted stack for Dokploy on the homelab box.

## Secrets

Values live in Dokploy env vars (`LLM_API_KEY`, `VOYAGE_API_KEY`, `DB_PASSWORD`) — none are committed here.

## Volumes (host bind mounts)

- `/srv/cognee/data` — Kuzu graph + cognee system files
- `/srv/cognee/postgres` — PostgreSQL + pgvector data

## Usage

Deployed via Dokploy (compose, git source). Push to `main` to redeploy.
