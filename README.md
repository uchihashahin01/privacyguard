# 🛡️ PrivacyGuard

<p align="center">
  <img src="docs/screenshot.png" alt="PrivacyGuard Screenshot" width="800">
</p>

<p align="center">
  <strong>Local-first privacy protection for your sensitive data</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#keyboard-shortcuts">Shortcuts</a> •
  <a href="#contributing">Contributing</a>
</p>

---

**PrivacyGuard** is a beautiful, modern Linux desktop application that scans text for personally identifiable information (PII) and secrets, replacing sensitive data with safe tokens—all processed locally on your machine. Perfect for sanitizing prompts before sending to AI assistants, cleaning logs, or redacting documents.

## ✨ Features

### 🔒 Privacy-First Design
- **100% Local Processing** - No data ever leaves your machine
- **No Cloud Dependencies** - Works completely offline
- **In-Memory Token Mapping** - Reversible redaction without file storage

### 🎯 Comprehensive Detection
| Category | What's Detected |
|----------|-----------------|
| 👤 **Names** | Personal names via NLP + pattern matching |
| 📧 **Emails** | Email addresses |
| 📱 **Phones** | Phone numbers with format validation |
| 🔑 **API Keys** | OpenAI, AWS, GitHub, Stripe, Google & more |
| 📍 **Addresses** | Physical addresses and locations |
| 🌐 **IPs** | IPv4 and IPv6 addresses |
| 💳 **Credit Cards** | Card numbers with Luhn validation |
| 🆔 **National IDs** | SSN and other national identifiers |
| 📅 **Dates of Birth** | Context-aware DOB detection |
| ⚙️ **Custom Rules** | Your own regex patterns and keywords |

### 🎨 Modern UI
- **Vibrant Gradient Design** - Beautiful purple/teal color scheme
- **Glassmorphism Effects** - Modern frosted glass aesthetics
- **Animated Interactions** - Smooth hover and focus effects
- **Dark Theme** - Easy on the eyes for extended use

### 🚀 Productivity Features
- **Drag & Drop** - Drop files directly into the app
- **File Import/Export** - Open and save text files
- **Keyboard Shortcuts** - Fast workflow with hotkeys
- **Statistics Panel** - See what was redacted at a glance
- **System Tray** - Minimize to tray, restore with a click
- **Quick Copy** - One-click copy for input and output

## 📦 Installation

### Prerequisites (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-venv python3-pip \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 \
    libgirepository-1.0-1 libcairo2 pkg-config
```

### Option 1: AppImage (Recommended)

Download the latest AppImage from [Releases](https://github.com/uchihashahin01/privacyguard/releases):

```bash
chmod +x PrivacyGuard-x86_64.AppImage
./PrivacyGuard-x86_64.AppImage
```

### Option 2: Debian Package

```bash
sudo dpkg -i privacyguard_*.deb
```

### Option 3: Install from Source

```bash
git clone https://github.com/uchihashahin01/privacyguard.git
cd privacyguard
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev,nlp,secrets]
```

Run the app:
```bash
python -m privacyguard.main
```

## 🎮 Usage

### Quick Start

1. **Paste or Drop** your text into the input panel
2. **Toggle** detection categories in the sidebar
3. **Click Redact** (or press `Ctrl+R`)
4. **Copy** the clean output with one click
5. **Restore** original values when needed

### Example

**Input:**
```
Contact John Smith at john.smith@company.com or call +1 (555) 123-4567.
His API key is sk-abc123xyz456 and IP is 192.168.1.100.
```

**Output:**
```
Contact [PERSON_1] at [EMAIL_1] or call [PHONE_1].
His API key is [OPENAI_KEY_1] and IP is [IPV4_1].
```

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Redact | `Ctrl+R` |
| Copy Clean Text | `Ctrl+Shift+C` |
| Restore Original | `Ctrl+Shift+R` |
| Clear All | `Ctrl+L` |
| Open File | `Ctrl+O` |
| Save Output | `Ctrl+S` |

## 🔧 Configuration

Access **Preferences** (gear icon) to configure:

- **GitHub Repository** - For update checks
- **spaCy Model** - Choose between speed and accuracy
- **Custom Regex** - Add your own detection patterns
- **Custom Keywords** - Specific words to always redact

## 🏗️ Architecture

```
privacyguard/
├── main.py              # Application entry point
├── config/              # Settings management
│   └── settings.py
├── engine/              # Redaction engine
│   ├── redactor.py      # Core orchestrator
│   ├── pii.py           # PII detection
│   ├── secrets.py       # Secret detection
│   ├── location.py      # Address detection
│   └── custom.py        # Custom rules
├── ui/                  # GTK4/Libadwaita UI
│   ├── window.py        # Main window
│   ├── preferences.py   # Settings dialog
│   └── system_integration.py
└── updater/             # Auto-update checker
```

## 🧪 Development

### Run Tests

```bash
python -m pytest tests/ -v
```

### Build Distributables

```bash
# AppImage
bash packaging/build_appimage.sh

# Debian package
bash packaging/build_deb.sh
```

### Code Style

```bash
pip install ruff
ruff check privacyguard/
```

## 🔐 Privacy Model

- ✅ All processing happens locally in-process
- ✅ No text or tokens are written to disk
- ✅ Update checks only query GitHub Releases metadata
- ✅ No telemetry or analytics
- ✅ No network requests during redaction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Run the test suite (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [spaCy](https://spacy.io/) - NLP processing
- [detect-secrets](https://github.com/Yelp/detect-secrets) - Secret detection
- [GTK4](https://gtk.org/) & [Libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/) - UI framework
- [pystray](https://github.com/moses-palmer/pystray) - System tray integration

---

<p align="center">
  Made with 💜 for privacy-conscious users
</p>
