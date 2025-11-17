# Novel Writer

> A streamlined desktop application for collaborative novel writing with AI agents

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **5 Specialized AI Agents**: Story Architect, Character & Dialogue Specialist, Prose & Atmosphere Writer, Research & Continuity Guardian, and Editorial Reviewer
- **Beautiful Dark-Mode UI**: Modern, distraction-free writing environment
- **Built-in Version Control**: Every change is tracked with Git
- **Autonomous File Management**: Agents can create, read, and modify project files
- **Real-time Streaming**: See agent responses as they're generated
- **Project Organization**: Structured folder system for planning, characters, manuscript, and more

## 🚀 Quick Start

### For End Users (Download & Install)

**Want to just use the app?** Download the installer for your platform:

- **Windows**: Download `.msi` installer → Run → Desktop shortcut appears ✨
- **macOS**: Download `.dmg` → Drag to Applications → Done ✨
- **Linux**: Download `.deb`/`.AppImage` → Install → Launch ✨

**No Python, Node, or Rust required** - everything is bundled!

See [Releases](#) for downloads.

---

### For Developers (Build from Source)

#### Automated Setup (Recommended)

**macOS/Linux**:
```bash
git clone https://github.com/yourusername/novel-writer.git
cd novel-writer
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows** (PowerShell):
```powershell
git clone https://github.com/yourusername/novel-writer.git
cd novel-writer
.\scripts\setup.ps1
```

The setup script automatically:
- Checks for Node.js, Python, Rust
- Installs all dependencies
- Builds the Python backend
- Sets up the development environment

#### Manual Setup

If you prefer manual setup:

**Prerequisites**:
- **Node.js** (v18 or higher)
- **Python** (3.9 or higher)
- **Rust** (latest stable)
- **Anthropic API Key** ([Get one here](https://console.anthropic.com/))

**Steps**:

1. **Clone and install**
   ```bash
   git clone https://github.com/yourusername/novel-writer.git
   cd novel-writer
   npm install
   ```

2. **Setup Python backend**
   ```bash
   cd python-backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller
   cd ..
   ```

3. **Start development servers**

   Terminal 1 - Backend:
   ```bash
   cd python-backend
   source venv/bin/activate
   python main.py --reload
   ```

   Terminal 2 - Frontend:
   ```bash
   npm run tauri:dev
   ```

4. **Configure API key**
   - Open the app
   - Click settings (⚙️)
   - Enter your Anthropic API key
   - Save

## 📖 Usage

### Creating a New Project

1. Launch Novel Writer
2. Fill in project details:
   - Novel title
   - Author name
   - Genre
   - Target word count
   - Project location
3. (Optional) Provide story context:
   - Core premise
   - Themes
   - Setting
   - Key characters
4. Click "Create Project"

### Working with Agents

1. **Select an agent** from the agent bar (Story Architect, Character Specialist, etc.)
2. **Type your message** describing what you want to work on
3. **Press Enter** or click Send
4. The agent will respond and may create/update files automatically
5. **Review changes** in the Project Explorer on the right

### Managing Files

- **View files**: Click any file in the Project Explorer to preview
- **Edit externally**: Files are standard markdown - open in your favorite editor
- **Version history**: Click the history icon to view and restore previous versions

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS + shadcn/ui
- **Desktop**: Tauri (Rust)
- **Backend**: Python FastAPI
- **AI**: Anthropic Claude API
- **Database**: SQLite
- **Version Control**: Git (libgit2)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed technical documentation.

## 📁 Project Structure

```
novel-writer/
├── src/                    # React frontend
│   ├── components/         # UI components
│   ├── lib/               # Utilities, types, state
│   └── styles/            # Global styles
├── src-tauri/             # Rust/Tauri backend
│   └── src/               # File & Git operations
├── python-backend/        # FastAPI server
│   ├── agents/            # AI agent system
│   ├── models/            # Database models
│   └── routes/            # API endpoints
├── docs/                  # Documentation
└── public/                # Static assets
```

## 🤖 The Five Agents

1. **Story Architect** 🏛️
   - Narrative structure and story arcs
   - Chapter and scene planning
   - Thematic development

2. **Character & Dialogue Specialist** 👤
   - Character creation and psychology
   - Authentic dialogue
   - Voice consistency

3. **Prose & Atmosphere Writer** ✍️
   - Scene writing with beautiful prose
   - Sensory details and atmosphere
   - Narrative voice

4. **Research & Continuity Guardian** 📚
   - Fact-checking and research
   - Story bible maintenance
   - Timeline tracking

5. **Editorial Reviewer** 🔍
   - Critical reading and feedback
   - Redundancy detection
   - Pacing analysis

See [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md) for detailed agent capabilities.

## 🛠️ Development

### Build Installers

**Quick Build** (one command):
```bash
npm run build:all
```

This creates production installers with the Python backend bundled:
- **Windows**: `.msi` and `.exe` in `src-tauri/target/release/bundle/msi/` and `nsis/`
- **macOS**: `.dmg` and `.app` in `src-tauri/target/release/bundle/dmg/` and `macos/`
- **Linux**: `.deb`, `.AppImage`, `.rpm` in `src-tauri/target/release/bundle/deb/`, `appimage/`, `rpm/`

**Separate Steps**:
```bash
# 1. Build Python backend
npm run backend:build

# 2. Build Tauri installers
npm run tauri:build
```

For detailed instructions, see [INSTALLER_GUIDE.md](INSTALLER_GUIDE.md).

### Running Tests

```bash
# Frontend tests
npm test

# Backend tests
cd python-backend
pytest
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Tauri](https://tauri.app/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/novel-writer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/novel-writer/discussions)
- **Email**: support@novelwriter.app

## 🗺️ Roadmap

- [ ] Cloud sync support
- [ ] Collaborative editing
- [ ] Export to EPUB/DOCX/PDF
- [ ] Custom agent templates
- [ ] Plugin system
- [ ] Mobile companion app

---

**Happy Writing! 📝✨**
