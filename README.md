# CursedContainer

CursedContainer - A Dockerized, set-it-and-forget-it mod synchronization tool for Hytale.

## Features
- Parses mod entries from [data/modlist.txt](data/modlist.txt)
- Supports inline mod entries through the `MODS` environment variable (multiline)
- Accepts full CurseForge URLs or plain slugs
- Downloads the latest main file for each Hytale mod from CurseForge
- Verifies downloads with SHA-1 before keeping files
- Tracks installed versions and sync history in [data/manifest.json](data/manifest.json)
- Replaces old files when a newer version is available

## Requirements
- Docker or a container engine
- [CurseForge API key](https://docs.curseforge.com/rest-api/#getting-started)

## Quick Start
1. Download one of the compose examples and set your API key in `.env`.
2. Add mods with either `MODS` in compose or `data/modlist.txt`.
3. Start the container with `docker compose up -d` (or `podman compose up -d`).

## Setup

Use these example files as starting points:
- Minimal example: [docker-compose-example.yml](docker-compose-example.yml)
- Podman example: [podman-compose-example.yml](podman-compose-example.yml)
- Full configuration example: [docker-compose-full-example.yml](docker-compose-full-example.yml)
- Full setup env template: [full-example.env](full-example.env)

> **Recommendation:** Use the compose example files as the source of truth. The inline snippets in this README are for quick reference and may become outdated.

### 1) Docker Compose

Source file: [docker-compose-example.yml](docker-compose-example.yml)

```yml
services:
    app:
        image: localhost/cursedcontainer_app
        userns_mode: "keep-id"
        user: "1000:1000"
        environment:
            CURSE_FORGE_API: ${CURSE_FORGE_API}
            MODS: |
                bettermap
                https://www.curseforge.com/hytale/mods/eyespyadmin-tools-reforged
        volumes:
            - ./data:/app/data:Z
            - ./mods:/app/mods:Z
```

```bash
wget -O docker-compose.yml https://raw.githubusercontent.com/alxan0/CursedContainer/main/docker-compose-example.yml
```

### or Podman Compose

Source file: [podman-compose-example.yml](podman-compose-example.yml)

```yml
services:
    app:
        image: ghcr.io/alxan0/cursedcontainer:latest
        userns_mode: "keep-id"
        user: "1000:1000"
        environment:
            CURSE_FORGE_API: ${CURSE_FORGE_API}
            MODS: |
                bettermap
                https://www.curseforge.com/hytale/mods/eyespyadmin-tools-reforged
        volumes:
            - ./data:/app/data:Z
            - ./mods:/app/mods:Z
```

```bash
wget -O docker-compose.yml https://raw.githubusercontent.com/alxan0/CursedContainer/main/podman-compose-example.yml
```

### 2) Create a `.env` file in the project root:
```env
CURSE_FORGE_API=your_api_key_here
```

### 3) Usage: The Modlist

CursedContainer reads from `data/modlist.txt` and also supports `MODS` from environment variables.

- `MODS` should be newline-separated (ideal for Compose `MODS: |` format).
- Entries from `MODS` are processed first, then entries from `data/modlist.txt`.
- Duplicates are removed after parsing/normalization, preserving first occurrence order.

You can add one mod per line. It accepts either the plain project slug or the full CurseForge URL.

**Example `data/modlist.txt`:**
```text
bettermap
https://www.curseforge.com/hytale/mods/eyespyadmin-tools-reforged
```

### 4) Run the container

```bash
docker compose up -d
```

For Podman:

```bash
podman compose up -d
```

## Automation / Server Restart

At the moment, CursedContainer does not restart the Hytale server automatically after updating mods.

For automated setups, use an orchestrated flow (for example in [docker-compose-full-example.yml](docker-compose-full-example.yml)) where:
1. The Hytale server waits while CursedContainer performs mod sync.
2. CursedContainer exits after updates are complete.
3. The Hytale server starts (or restarts) after the sync step finishes.

You can coordinate this with container startup order, a small wrapper script, or a scheduler such as `cron`.

## Configuration Variables

`CURSE_FORGE_API` **or** `CURSE_FORGE_API_FILE` must be provided.
| Environment Variable | Description | Default | Required |
| :------------------- | :---------- | :------ | :------- |
| `CURSE_FORGE_API` | CurseForge Core API key as plain env var. | None | One of `CURSE_FORGE_API` / `CURSE_FORGE_API_FILE` |
| `CURSE_FORGE_API_FILE` | Path to a file containing the CurseForge API key (recommended for container secrets). | None | One of `CURSE_FORGE_API` / `CURSE_FORGE_API_FILE` |
| `APP_BASE_PATH` | Base path used for `data/` and `mods/` directories. | current working directory | No |
| `SYNC_INTERVAL` | Time between sync runs in hours (`0` = run once and exit). | `0` | No |
| `MAX_MOD_FILE_SIZE_MB` | Maximum allowed mod file size in MB. | `1024` | No |
| `DOWNLOAD_TIMEOUT_SECONDS` | Read/write timeout for HTTP requests. | `60` | No |
| `CONNECT_TIMEOUT_SECONDS` | Connection timeout for HTTP requests. | `10` | No |
| `APP_TIMEZONE` | Timezone used for manifest timestamps (IANA format, e.g. `Europe/Stockholm`). | `UTC` | No |
| `MODS` | Newline-separated mod entries from environment `MODS: \|` in Compose. Merged with `data/modlist.txt`; duplicates removed. | empty | No |

## Roadmap
- Add support for selecting a mod release channel (`stable` or `beta`) and an optional target version.
