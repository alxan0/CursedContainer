# CursedContainer

CursedContainer - A Dockerized, set-it-and-forget-it mod synchronization tool for Hytale.

## Features
- Parses mod entries from [data/modlist.txt](data/modlist.txt)
- Accepts full CurseForge URLs or plain slugs
- Downloads the latest main file for each Hytale mod from CurseForge
- Verifies downloads with SHA-1 before keeping files
- Tracks installed versions and sync history in [data/manifest.json](data/manifest.json)
- Replaces old files when a newer version is available

## Requirements
- Docker or a container engine
- [CurseForge API key](https://docs.curseforge.com/rest-api/#getting-started)
## Setup

### 1) Docker Compose

```yml
services:
    app:
        image: localhost/cursedcontainer_app
        user: "1000:1000"
        environment:
            - CURSE_FORGE_API=${CURSE_FORGE_API}
        volumes:
        - ./data:/app/data
        - ./mods:/app/mods
```

### or Podman Compose

```yml
services:
    app:
        image: localhost/cursedcontainer_app
        userns_mode: "keep-id"
        user: "1000:1000"
        environment:
            - CURSE_FORGE_API=${CURSE_FORGE_API}
        volumes:
        - ./data:/app/data:Z
        - ./mods:/app/mods:Z
```

### 2) Create a `.env` file in the project root:
```env
CURSE_FORGE_API=your_api_key_here
```

### 3) Usage: The Modlist

CursedContainer reads from `data/modlist.txt`. You can add one mod per line. It accepts either the plain project slug or the full CurseForge URL.

**Example `data/modlist.txt`:**
```text
bettermap
https://www.curseforge.com/hytale/mods/eyespyadmin-tools-reforged
```

##  Configuration Variables

| Environment Variable | Description                                                          | Required |
| :------------------- | :------------------------------------------------------------------- | :------- |
| `CURSE_FORGE_API`    | Your CurseForge Core API Key.                                        | **Yes**  |
| `APP_BASE_PATH`      | The internal base path for the app (uses relative paths by default). | No       |
| `SYNC_INTERVAL`      | The time interval between update checks.                             | No       |

