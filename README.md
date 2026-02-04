# Swiss Jobs Scraper 🇨🇭

[![CI](https://github.com/yourrepo/swiss-jobs-scrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/yourrepo/swiss-jobs-scrapper/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A production-grade, extensible job aggregation engine for the Swiss market.**

Designed for reliability, stealth, and AI integration, this tool scrapes high-quality job data from federal portals (job-room.ch) while handling complexity like BFS codes, anti-bot protection, and multilingual content.

## ✨ Key Features

- **🔍 Advanced Search**: Filter by location, workload (%), contract type, work forms, language skills, and more.
- **🇨🇭 Swiss-Optimized**: Native support for **BFS communal codes**, canton filtering, and multilingual content (DE/FR/IT/EN).
- **🛡️ Stealth Technology**: Built-in browser fingerprint simulation, CSRF handling, and TLS fingerprint evasion.
- **⚡ Flexible Execution**: Choose between `Fast`, `Stealth`, or `Aggressive` modes depending on your needs.
- **🤖 Atomic AI Processing**: Optional AI features to translate, extract experience levels, identifying required languages, and generate keywords.
- **🔌 Dual Interface**: Full CLI suite and a REST API (FastAPI) for seamless integration.

---

## 🚀 Quick Start

### Docker (Recommended)
The easiest way to get started is using the pre-built Docker image.

```bash
# Pull and run
docker pull swiss-jobs-scraper:latest
docker run -p 8000:8000 swiss-jobs-scraper
```

### CLI
```bash
# Install via pip
pip install swiss-jobs-scraper

# Quick search for engineering jobs in Zurich
swiss-jobs search "Software Engineer" --location Zurich
```

---

## 📚 Documentation

For complete details on configuration, the REST API, architecture, and database schema, please refer to the comprehensive [DOCUMENTATION.md](DOCUMENTATION.md).

### What's Inside?
- **System Overview**: Understanding the 4-layer architecture.
- **API Reference**: Detailed endpoint documentation.
- **CLI Manual**: All commands and flags explained.
- **Database Schema**: Full PostgreSQL table definitions.
- **Technical Deep Dive**: How BFS resolution and Stealth Mode work.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## ⚖️ Legal

This tool is for educational and legitimate data aggregation purposes only. Respect `robots.txt`, rate limits, and Swiss data protection laws (nFADP).

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
