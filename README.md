# 🚀 AGI Prospection Hub — Elite B2B Intelligence

![Version](https://img.shields.io/badge/version-v1.1.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![AGI](https://img.shields.io/badge/AI-Agentic-orange?style=for-the-badge)

**AGI Prospection Hub** is a powerful, autonomous sales engine built on top of the Onyx framework. It transforms raw business data into high-conversion outreach opportunities using elite sales methodologies.

---

## ✨ Key Features

### 🤖 Agentic Sales Intelligence
- **Dataset Ingestion**: Native support for Google Places & Apify JSON datasets.
- **Auto-ICP Scoring**: Intelligent lead qualification based on company size, industry fit, and pain signals.
- **Multi-Agent Orchestration**: Spawn specialized sub-agents for different niches or campaigns.

### 📡 Integrated Outreach Suite
- **Telegram Notifications**: Real-time push alerts for high-value prospects.
- **Twilio SMS & Voice**: Automated multi-channel communication (Text & Call).
- **Elite Scripting**: Built-in frameworks for **Charlie Morgan** (Loom), **Aaron Shepherd** (Email), and **Jordan Platten** (Call).

### 🎨 Premium Experience
- **Deep Oceanic UI**: Stunning dark mode designed for focus and performance.
- **Full i18n**: Fully localized in French and English.
- **Modern Stack**: Next.js, FastAPI, PostgreSQL, Vespa, and Redis.

---

## 🛠️ Quick Start

### 1. Deployment Options

We provide a unified deployment script for ease of use.

#### **Via PowerShell (Modern)**
```powershell
# Default (Docker)
.\deploy.ps1

# Local Development (No Docker)
.\deploy.ps1 -Mode local

# Stop services
.\deploy.ps1 -Stop
```

#### **Via Batch (One-Click)**
Simply double-click `deploy.bat` to launch the Docker environment.

### 2. Configuration
Open `deployment/docker_compose/.env` and configure your API keys:
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, & `TWILIO_PHONE_NUMBER`
- `AGI_DATASET_DIR` (Default: `/app/custom_knowledge`)

---

## 📁 Project Structure
- `/backend`: Core AGI engine and prospection tools.
- `/web`: Premium Next.js frontend with i18n.
- `/deployment`: Docker orchestration and environment configs.
- `/custom_knowledge`: Target directory for your JSON/CSV datasets.

---

## 🤝 Contribution
Designed for elite sales agencies. For custom integrations or feature requests, please open an issue or submit a PR.

---

**Built with ❤️ for High-Performance Prospection.**
