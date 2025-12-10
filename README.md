# Power Transformer Designer

A full-stack web application for designing power transformers, inductors, and pulse transformers using industry-standard methodologies including McLyman's Area Product (Ap) and Core Geometry (Kg) methods.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Nuxt](https://img.shields.io/badge/Nuxt-3.14+-00DC82.svg)](https://nuxt.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Features

### Design Methods
- **McLyman's Ap Method**: Classic area product approach for initial transformer sizing
- **McLyman's Kg Method**: Core geometry method optimized for high-power designs
- **Erickson's Kgfe Method**: Loss-optimized design for high-frequency applications
- **Pulse Transformer Design**: Specialized design for capacitor-discharge pulse applications
- **Inductor Design**: Energy storage method with air gap calculations

### Analysis Capabilities
- **Loss Analysis**: Core losses (Steinmetz equation) and copper losses with AC effects
- **Thermal Analysis**: Temperature rise prediction and thermal management
- **Cross-Validation**: Multi-method confidence scoring for design verification
- **Winding Design**: Optimal conductor sizing, turns calculation, and layer configuration

### Database Integration
- **Local Core Database**: 100+ ferrite and silicon steel cores with detailed specifications
- **OpenMagnetics Integration**: Access to 10,000+ cores from major manufacturers (TDK, Ferroxcube, Ferrіte, etc.)
- **Material Database**: Comprehensive material properties and Steinmetz coefficients
- **Loss-Based Core Selection**: Intelligent core selection optimized for minimum losses

### Export Capabilities
- **MAS JSON**: OpenMagnetics-compatible format for FEA tools
- **FEMM Lua Scripts**: Direct export for Finite Element Method Magnetics simulation
- **Design Archives**: Complete design data in JSON format for documentation

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (managed via [uv](https://github.com/astral-sh/uv))
- **Node.js 18+** and npm
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd transformer_designer
   ```

2. **Backend Setup**
   ```bash
   cd backend
   uv sync
   uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
   
   API documentation available at: http://localhost:8000/docs

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   
   Web interface available at: http://localhost:3000

## 📁 Project Structure

```
transformer_designer/
├── backend/                    # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── calculations/          # Core design algorithms
│   │   ├── ap_method.py      # McLyman's Ap method
│   │   ├── kg_method.py      # McLyman's Kg method
│   │   ├── erickson_method.py # Erickson's Kgfe method
│   │   ├── pulse_transformer.py # Pulse transformer design
│   │   ├── winding.py        # Winding calculations
│   │   ├── losses.py         # Loss analysis
│   │   ├── thermal.py        # Thermal analysis
│   │   └── cross_validation.py # Design validation
│   ├── models/               # Pydantic data models
│   ├── routers/              # API endpoints
│   ├── integrations/         # External integrations
│   │   ├── openmagnetics.py # OpenMagnetics API
│   │   ├── mas_exporter.py  # MAS format export
│   │   └── silicon_steel.py # Silicon steel cores
│   ├── data/                # Core and material databases
│   └── tests/               # Comprehensive test suite
├── frontend/                # Nuxt 3 frontend
│   ├── pages/              # Application pages
│   │   ├── index.vue      # Home page
│   │   └── design/        # Design interfaces
│   ├── components/        # Vue components
│   ├── composables/       # Composable functions
│   └── assets/           # Styles and static assets
├── pdfs/                  # Reference documentation
└── README.md             # This file
```

## 🛠️ Usage

### Transformer Design

1. Navigate to **Design → Transformer** (`/design/transformer`)
2. Enter your requirements:
   - **Power**: Output power (W)
   - **Frequency**: Switching frequency (Hz)
   - **Voltages**: Primary and secondary voltages
   - **Topology**: Forward, flyback, push-pull, etc.
   - **Duty Cycle**: Operating duty cycle
   - **Waveform**: Square, sine, trapezoidal

3. View results:
   - Selected core with specifications
   - Winding configuration (turns, wire gauge, layers)
   - Loss breakdown (core + copper losses)
   - Temperature rise estimate
   - Alternative core suggestions with OpenMagnetics integration

### Inductor Design

1. Navigate to **Design → Inductor** (`/design/inductor`)
2. Specify parameters:
   - **Inductance**: Required inductance value (H)
   - **Current**: DC and peak current (A)
   - **Ripple**: Current ripple percentage
   - **Frequency**: Operating frequency (Hz)

3. Results include:
   - Core selection with air gap
   - Number of turns
   - Wire specifications
   - Saturation margin

### Pulse Transformer Design

1. Navigate to **Design → Pulse** (`/design/pulse`)
2. Enter pulse specifications:
   - **Source Capacitor**: Capacitance and voltage
   - **Pulse Width**: Duration of pulse
   - **Repetition Rate**: Pulse frequency
   - **Isolation**: Required voltage isolation
   - **Load Impedance**: Output load characteristics

3. Get specialized pulse design with:
   - Core sized for volt-second product
   - Winding configuration for low-leakage
   - Isolation considerations
   - Energy transfer efficiency

## 🔌 API Endpoints

### Design Endpoints
- `POST /api/design/transformer` - Design a power transformer
- `POST /api/design/inductor` - Design an inductor
- `POST /api/design/pulse` - Design a pulse transformer

### Database Endpoints
- `GET /api/cores` - List all available cores
- `GET /api/materials` - List material properties
- `GET /api/openmagnetics/cores` - Search OpenMagnetics database
- `GET /api/openmagnetics/cores/{shape}` - Get cores by shape

### Export Endpoints
- `POST /api/export/mas` - Export to MAS JSON format
- `POST /api/export/femm` - Export to FEMM Lua script
- `POST /api/export/json/download` - Download design as JSON

### Utility Endpoints
- `GET /health` - Health check
- `GET /` - API information and endpoints

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd backend
uv run pytest
```

Test coverage includes:
- Design method algorithms
- Loss calculations
- Thermal analysis
- Winding calculations
- API endpoint validation
- Integration tests

## 🎓 Design Methods Explained

### McLyman's Ap Method
The Area Product method is ideal for initial transformer sizing:
- **Ap = Wa × Ac** (window area × core area)
- Fast, reliable approximation
- Best for: Initial estimates, simple designs

### McLyman's Kg Method
Core Geometry method for optimized designs:
- **Kg = Ap² / MLT** (area product squared / mean length per turn)
- Better core utilization for high power
- Best for: Power transformers, optimized designs

### Erickson's Kgfe Method
Loss-optimized design for high efficiency:
- Minimizes total losses (core + copper)
- Accounts for frequency-dependent effects
- Best for: High-frequency converters, efficiency-critical applications

## 📊 Export Formats

### MAS JSON (OpenMagnetics)
Standard format compatible with OpenMagnetics tools and FEA software:
- Complete magnetic model
- Winding specifications
- Material properties
- Geometry definitions

### FEMM Lua Scripts
Direct export for electromagnetic simulation:
- Automated geometry creation
- Material assignments
- Excitation setup
- Boundary conditions

## 🔧 Development

### Backend Development
```bash
cd backend
uv run uvicorn main:app --reload  # Auto-reload on changes
```

### Frontend Development
```bash
cd frontend
npm run dev  # Hot module replacement enabled
```

### Adding New Cores
Edit [`backend/data/cores.json`](backend/data/cores.json) following the existing format:
```json
{
  "name": "ETD39",
  "Ae": 125e-6,
  "Aw": 124e-6,
  "Ve": 16000e-9,
  "MLT": 81.5e-3,
  ...
}
```

### Adding New Materials
Edit [`backend/data/materials.json`](backend/data/materials.json) with Steinmetz coefficients:
```json
{
  "name": "3F3",
  "Kc": 48.4,
  "alpha": 1.32,
  "beta": 2.6,
  ...
}
```

## 📚 References

This tool implements methodologies from:

1. **Colonel Wm. T. McLyman** - *Transformer and Inductor Design Handbook* (4th Edition, 2011)
   - Area Product (Ap) method
   - Core Geometry (Kg) method
   - Winding design principles

2. **Robert W. Erickson** - *Fundamentals of Power Electronics*
   - Kgfe loss-optimized design
   - High-frequency effects
   - Converter topologies

3. **OpenMagnetics Standard** - MAS format specification
   - Industry-standard magnetic model format
   - FEA tool compatibility

## 🤝 Contributing

Contributions are welcome! Key areas for improvement:

- Additional core geometries and manufacturers
- Enhanced thermal modeling
- More converter topologies
- UI/UX enhancements
- Test coverage expansion

## 📝 Documentation

- **User Guide**: [`user_guide.md`](user_guide.md) - Detailed usage instructions
- **Backend README**: [`backend/README.md`](backend/README.md) - Backend-specific details
- **API Documentation**: http://localhost:8000/docs (when running)
- **Project Structure**: [`project_structure_report.md`](project_structure_report.md)

## 🔍 Troubleshooting

### Backend won't start
- Ensure Python 3.11+ is installed
- Run `uv sync` to install dependencies
- Check port 8000 is available

### Frontend connection issues
- Verify backend is running on port 8000
- Check CORS settings in [`backend/main.py`](backend/main.py:47)
- Clear browser cache and reload

### No cores found
- Verify [`backend/data/cores.json`](backend/data/cores.json) exists
- Check file permissions
- Review backend logs for database loading errors

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- McLyman's seminal work on magnetics design
- OpenMagnetics project for database integration
- FastAPI and Nuxt communities
- Open-source power electronics community

---

**Version**: 0.3.0  
**Status**: Active Development  
**Last Updated**: December 2025