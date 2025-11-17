# Contributing to Novel Writer

Thank you for your interest in contributing to Novel Writer! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/novel-writer/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, version, etc.)

### Suggesting Features

1. Check if the feature has been suggested in [Issues](https://github.com/yourusername/novel-writer/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Use case and rationale
   - Proposed implementation (if you have ideas)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation if needed

4. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
   - Use clear, descriptive commit messages
   - Reference issues if applicable (#123)

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**
   - Provide a clear description of changes
   - Reference related issues
   - Include screenshots for UI changes

## Development Setup

### Prerequisites

- Node.js 18+
- Python 3.9+
- Rust (latest stable)

### Setup

1. Clone your fork
   ```bash
   git clone https://github.com/yourusername/novel-writer.git
   cd novel-writer
   ```

2. Install dependencies
   ```bash
   npm install
   cd python-backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd ..
   ```

3. Run development servers
   ```bash
   # Terminal 1: Backend
   cd python-backend
   source venv/bin/activate
   uvicorn main:app --reload

   # Terminal 2: Frontend
   npm run tauri:dev
   ```

## Code Style

### TypeScript/React

- Use TypeScript strict mode
- Prefer functional components
- Use meaningful variable names
- Add JSDoc comments for complex functions

### Python

- Follow PEP 8
- Use type hints
- Add docstrings to functions/classes
- Use Black for formatting

### Rust

- Follow Rust conventions
- Use `cargo fmt` for formatting
- Use `cargo clippy` for linting

## Testing

### Frontend
```bash
npm test
```

### Backend
```bash
cd python-backend
pytest
```

## Documentation

- Update README.md if you add features
- Update relevant docs in `docs/` folder
- Add code comments for complex logic

## Areas for Contribution

We especially welcome contributions in:

- **Bug fixes**: Always appreciated!
- **UI/UX improvements**: Make the app more beautiful and usable
- **Agent enhancements**: Improve agent prompts and capabilities
- **Export features**: EPUB, DOCX, PDF generation
- **Testing**: Increase test coverage
- **Documentation**: Improve guides and tutorials
- **Performance**: Optimize slow operations
- **Accessibility**: Make the app more accessible

## Questions?

Feel free to open an issue with the "question" label or reach out in [Discussions](https://github.com/yourusername/novel-writer/discussions).

## Thank You!

Your contributions make Novel Writer better for everyone. We appreciate your time and effort! 🙏
