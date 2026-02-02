# Swiss Jobs Scraper 🇨🇭

[![CI](https://github.com/yourrepo/swiss-jobs-scrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/yourrepo/swiss-jobs-scrapper/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-grade, extensible job scraper for the Swiss job market. Designed for reliability, stealth, and ease of integration.

Currently supports **job-room.ch** (the official Swiss federal job portal) with an architecture built for easy addition of future providers.

## ✨ Key Features

- **🔍 Advanced Search**: Filter by location, workload (%), contract type, work forms, language skills, and more.
- **🇨🇭 Swiss-Optimized**: Native support for BFS communal codes, canton filtering, and multilingual content (DE/FR/IT/EN).
- **🛡️ Stealth Technology**: Built-in browser fingerprint simulation, CSRF handling, and TLS fingerprint evasion.
- **⚡ Flexible Execution**: Choose between `Fast`, `Stealth`, or `Aggressive` modes depending on your needs.
- **🤖 Atomic AI Processing**: Optional AI features to translate, extract experience levels, identifying required languages, and generate keywords.
- **💾 Remote Persistence**: Optional PostgreSQL integration with automatic deduplication and change tracking.
- **🔌 Dual Interface**: Full CLI suite and a REST API (FastAPI) for seamless integration.

> 📚 **Deep Dive**: Check out [DOCUMENTATION.md](DOCUMENTATION.md) for a comprehensive reference manual covering CLI commands, API endpoints, architecture, and configuration details.

---

## 🚀 Installation

### Using pip

```bash
# Core installation
pip install swiss-jobs-scraper

# With optional features
pip install swiss-jobs-scraper[database]   # PostgreSQL support
pip install swiss-jobs-scraper[ai]         # AI features (Gemini/Groq)
pip install swiss-jobs-scraper[all]        # Everything
```

### Using Docker

```bash
# Pull and run the latest image
docker pull swiss-jobs-scraper:latest
docker run -p 8000:8000 swiss-jobs-scraper
```

### From Source (Poetry)

```bash
git clone https://github.com/yourrepo/swiss-jobs-scrapper.git
cd swiss-jobs-scrapper
poetry install --all-extras
poetry shell
```

---

## ⚙️ Configuration

Configure the application via a `.env` file or environment variables.

### Core Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `production` | Environment (production/development) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `API_PORT` | `8000` | Port for the API server |
| `WORKERS`  | `4`    | Number of API workers |

### Database (Optional)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Full connection string (e.g., `postgresql+asyncpg://...`) |
| *OR Components* | `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD` |

### AI Processing (Optional)
| Variable | Description |
|----------|-------------|
| `AI_PROVIDER` | `gemini` or `groq` |
| `AI_API_KEY` | Your API key |
| `AI_MODEL` | Override default model (e.g., `gemini-1.5-flash`) |

---

## 📖 Usage

### Command Line Interface (CLI)

The `swiss-jobs` command provides a powerful interface for interactive or scripted usage.

```bash
# 1. Quick Search
swiss-jobs search "Software Engineer" --location Zurich

# 2. Advanced Filtering
swiss-jobs search "Data Scientist" \
    --canton ZH --canton BE \
    --workload-min 80 \
    --contract permanent \
    --days 7 \
    --format table

# 3. Save to Database
swiss-jobs search "DevOps" --save

# 4. Apply AI Processing
swiss-jobs search "Product Owner" --ai --feature translation --feature experience
```

### REST API

Start the server using `swiss-jobs serve`. Interactive docs available at `http://localhost:8000/docs`.

**Quick Search:**
```http
GET /jobs/search/quick?query=Python&location=Bern
```

**Advanced Search (POST):**
```bash
curl -X POST http://localhost:8000/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Frontend Developer",
    "canton_codes": ["GE"],
    "language_skills": ["en"]
  }'
```

---

## 🧠 AI Capabilities

Enable granular AI processing to enrich job data.

**Atomic Features:**
- `translation`: Translate title/description to EN/DE/FR/IT.
- `experience`: Extract seniority level (Junior, Mid, Senior, etc.) and years of experience.
- `languages`: Identify required spoken languages.
- `education`: Extract education requirements.
- `keywords`: Generate semantic keywords for better indexing.

**Example Command:**
```bash
swiss-jobs search "Manager" --ai --feature translation --feature keywords
```

---

## 📦 Database Integration

Data persistence is handled via **PostgreSQL** with smart upsert logic.

- **Deduplication**: Jobs are tracked by ID.
- **Change Detection**: Content hashing detects changes in title or description, updating `date_updated`.
- **History**: Keeps track of when jobs were first added and last seen.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment, run tests, and submit pull requests.

## ⚖️ Legal Disclaimer

This tool is for educational and legitimate data aggregation purposes only.
1. Respect `robots.txt` and rate limits.
2. Comply with Swiss data protection laws (nFADP).
3. Do not use for unauthorized commercial redistribution.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
