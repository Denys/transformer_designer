# Power Transformer Designer - Backend

FastAPI backend implementing McLyman's Ap/Kg methodology for transformer and inductor design.

## Features

- **Transformer Design**: Area Product (Ap) and Core Geometry (Kg) methods
- **Inductor Design**: Energy storage method with gap calculation
- **Core Database**: Ferrite and silicon steel cores
- **Material Database**: Material properties and Steinmetz coefficients
- **Loss Analysis**: Core loss (Steinmetz) and copper loss with AC effects
- **Thermal Analysis**: Temperature rise prediction

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn main:app --reload

# Open API docs
# http://localhost:8000/docs
```

## API Endpoints

- `POST /api/design/transformer` - Design a transformer
- `POST /api/design/inductor` - Design an inductor
- `GET /api/cores` - List available cores
- `GET /api/materials` - List available materials
- `GET /health` - Health check
