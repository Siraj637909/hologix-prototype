# HOLOGIX - Personal AI API Infrastructure

Production-grade self-hosted personal AI API infrastructure and ultra-efficient local inference operating system.

## Overview

HOLOGIX converts weak consumer hardware into a secure local multimodal AI server that exposes OpenAI-compatible APIs.

### Core Features

- Local AI model execution
- Downloadable model library
- OpenAI compatible REST endpoints
- Personal API keys
- Future vision/audio/video inference
- Weak hardware optimization
- Secure local serving
- Desktop and CLI controls

## Monorepo Structure

```
HOLOGIX/
 ├── hologix_api/          # FastAPI backend, routes, schemas, middleware
 ├── hologix_core/         # Configuration, logging, exceptions, utilities
 ├── hologix_engine/       # C++ inference engine and bindings
 ├── hologix_desktop/      # Electron desktop application
 ├── hologix_sdk_python/   # Python SDK
 ├── hologix_sdk_js/       # JavaScript SDK
 ├── hologix_installers/   # Installation scripts for Linux, Windows, macOS
 ├── hologix_docs/         # API documentation and guides
 ├── hologix_tests/        # Unit, integration, and E2E tests
 └── hologix_web/          # Web interface
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m hologix_api.main

# Or use the CLI
hologix serve --port 8080
```

## License

MIT License
