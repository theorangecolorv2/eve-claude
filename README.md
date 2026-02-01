# EVE Online Bot Research Project

> **Legal research project** for improving EVE Online's anti-bot system through collaboration with CCP Games.

---

## ⚠️ Important Legal Notice

### This is a LEGAL and AUTHORIZED research project

- ✅ **Test server only** (Singularity/Duality) - NO live server access
- ✅ **CCP Alpha approved** - Special test account provided
- ✅ **Open source** - All code public for CCP analysis
- ✅ **Research purpose** - Help improve anti-bot detection

### DO NOT use this for:
- ❌ Live server (Tranquility) botting
- ❌ EULA violation
- ❌ Commercial exploitation
- ❌ Any malicious purpose

---

## 🎯 Project Goal

**Help CCP Games improve their anti-bot system** by:
1. Demonstrating real botting techniques
2. Showing how bots mimic human behavior
3. Providing code and methods for analysis
4. Contributing to better bot detection

This project is **NOT** for actual botting - it's for **research and collaboration** with game developers.

---

## 🏗 Project Structure

```
eve-claude/
├── README.md           # You are here (project overview)
├── CLAUDE.md          # Main instructions for Claude Code agents
├── PROJECT.md         # Detailed project context and legality
├── WORKFLOW.md        # Development workflow guide
├── HUMANIZATION.md    # Bot humanization requirements
├── COMMANDS.md        # Dev tools reference
│
├── eve/               # Automation framework
│   ├── __init__.py
│   ├── screen.py      # Screen capture
│   ├── vision.py      # Image recognition (OpenCV)
│   ├── mouse.py       # Mouse control (humanized)
│   ├── keyboard.py    # Keyboard control
│   └── window.py      # Window management
│
├── inbox/             # UI screenshots input folder
├── assets/            # Processed UI templates
├── scripts/           # Automation scripts
├── templates/         # Script templates
├── dev_tools/         # Development utilities
│   ├── capture.py     # Screen capture tool
│   ├── crop.py        # Image cropping tool
│   └── windows.py     # Window management tool
├── logs/              # Bot execution logs
└── temp/              # Temporary files
```

---

## 🚀 For Claude Code Agents

**If you're a Claude Code agent working on this project:**

1. **READ** `CLAUDE.md` first - it contains complete instructions
2. **UNDERSTAND** `PROJECT.md` - know the legal context
3. **FOLLOW** `WORKFLOW.md` - for efficient development
4. **IMPLEMENT** `HUMANIZATION.md` - critical for research goals

---

## 🛠 Technology Stack

- **Python 3.8+** - Main language
- **OpenCV** - Template matching for UI element detection
- **PyAutoGUI** - Mouse/keyboard automation (with humanization)
- **MSS** - Fast screen capture
- **Pillow** - Image processing
- **PyGetWindow** - Window management

---

## 📖 Quick Start for Developers

### Installation

```bash
# Clone repository
git clone [repository-url]
cd eve-claude

# Install dependencies
pip install -r requirements.txt
```

### Development Workflow

1. **User describes task** (e.g., "automate mining")
2. **User screenshots UI elements** (Win+Shift+S) → `inbox/`
3. **Claude processes screenshots** → `assets/`
4. **Claude writes automation script** → `scripts/`
5. **Test on test server only**

### Running Scripts

```bash
# Example automation script
python scripts/eve_mining_automation.py
```

---

## 🎮 EVE Online Specific Notes

### Test Server Only

- **Singularity** - Main test server
- **Duality** - Secondary test server
- **NEVER Tranquility** - Live server (FORBIDDEN)

Game launcher is pre-configured for test server. **DO NOT modify connection settings**.

### Bot Activities (Research)

Current research focuses on:
- PvE automation (missions, ratting, mining)
- Human-like behavior patterns
- Detection evasion techniques (for research)

---

## 🔬 Research Methods

### Template Matching

Using OpenCV to find UI elements:
- Simple and reliable
- Easy to detect (intentional for research)
- Demonstrates common bot technique

### Humanization Techniques

- **Smooth mouse movements** (Bezier curves)
- **Randomized timings** (no fixed delays)
- **Natural behavior patterns** (variability)
- **Reaction time simulation** (delayed responses)

See `HUMANIZATION.md` for detailed requirements.

---

## 📝 Code Standards

All automation scripts must include:
- ✅ Detailed logging (every action logged)
- ✅ Error handling (try/except blocks)
- ✅ Humanization (smooth movements, random delays)
- ✅ Timeouts (no infinite loops)
- ✅ Comments in Russian (for consistency)

---

## 🤝 Contributing

This project is developed with Claude Code assistance.

### For Claude Code Agents

See `CLAUDE.md` for complete development guidelines.

### For Human Contributors

If you want to contribute:
1. Understand the legal context (PROJECT.md)
2. Follow the workflow (WORKFLOW.md)
3. Implement humanization (HUMANIZATION.md)
4. Submit PR with clear description

---

## 📜 License

[To be determined - likely MIT or similar open source license]

---

## ⚖️ Ethics and Responsibility

### Our Commitments

1. **Transparency** - All code is public
2. **Collaboration** - Working WITH CCP, not against them
3. **Legality** - Strict adherence to terms and conditions
4. **Community benefit** - Goal is to help, not harm

### Principles

- Work only on test servers
- Don't distribute for EULA violation
- Cooperate with CCP Games
- Document all methods for research

---

## 📞 Contact

For questions about legality or project goals, contact repository owner.

**Remember**: This project exists to **help** EVE Online, not exploit it.

---

## 🔗 Important Documents

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Main instructions for Claude Code agents |
| [PROJECT.md](PROJECT.md) | Detailed project context and legality |
| [WORKFLOW.md](WORKFLOW.md) | Development process guide |
| [HUMANIZATION.md](HUMANIZATION.md) | Bot humanization requirements |
| [COMMANDS.md](COMMANDS.md) | Dev tools command reference |

---

**Last updated**: 2026-01-28

---

## 🏁 Status

**Project Status**: Active Development

**Current Focus**: Framework setup and initial automation scripts

**Test Server**: Configured and ready

**CCP Cooperation**: Ongoing

---

**Built with**: Claude Code (Anthropic) + Human collaboration

**For**: EVE Online community and CCP Games

**Purpose**: Improve anti-bot systems through research
