# Contributing to Hephaestus

Thank you for your interest in contributing to Hephaestus! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 20+ and npm
- Docker (for Qdrant)
- tmux
- Git
- Claude Code (for testing agent functionality)

### Development Setup

1. **Clone and setup the repository**
   ```bash
   git clone https://github.com/Ido-Levi/Hephaestus.git
   cd Hephaestus
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start required services**
   ```bash
   # Terminal 1: Qdrant
   docker run -d -p 6333:6333 qdrant/qdrant

   # Terminal 2: Frontend
   cd frontend
   npm install
   npm run dev
   ```

5. **Initialize databases**
   ```bash
   python scripts/init_db.py
   python scripts/init_qdrant.py
   ```

6. **Run the server**
   ```bash
   python run_server.py
   ```

## 📋 How to Contribute

### Reporting Bugs

Found a bug? Please open an issue using the **Bug Report** template. Include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Have an idea? Open a **Feature Request** issue with:
- Clear use case description
- Why this feature would be valuable
- Proposed implementation approach (if you have one)

### Submitting Code

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Make your changes**
   - Write clear, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run tests
   pytest

   # Check code style
   black src/ tests/
   flake8 src/ tests/

   # Type checking
   mypy src/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add clear description of your changes"
   ```

   Follow conventional commit format:
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a PR on GitHub with:
   - Clear title and description
   - Link to related issues
   - Screenshots/videos if UI changes
   - Test results

## 🎨 Code Style Guidelines

### Python

- Follow PEP 8
- Use type hints for function parameters and returns
- Write docstrings for classes and functions
- Maximum line length: 100 characters
- Use `black` for formatting

**Example:**
```python
def create_task(
    description: str,
    phase_id: int,
    agent_id: str,
    priority: str = "medium"
) -> str:
    """
    Create a new task for an agent.

    Args:
        description: Task description
        phase_id: Phase ID (1, 2, 3, etc.)
        agent_id: ID of the agent to assign
        priority: Task priority (low, medium, high, critical)

    Returns:
        Task ID string
    """
    # Implementation
    pass
```

### TypeScript/React

- Use TypeScript for all frontend code
- Functional components with hooks
- Use TanStack Query for API calls
- Follow existing component structure

### Documentation

- Update README.md for user-facing changes
- Update relevant docs in `website/docs/` for new features
- Add JSDoc/docstrings for new functions
- Include examples in documentation

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for new features
- Maintain or improve code coverage
- Use pytest fixtures for common setup
- Mock external services (LLM APIs, Qdrant)

**Example:**
```python
def test_create_task(mock_db, mock_llm):
    """Test task creation with mocked dependencies."""
    result = create_task(
        description="Test task",
        phase_id=1,
        agent_id="test-agent"
    )
    assert result.startswith("task-")
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_mcp_server.py

# With coverage
pytest --cov=src --cov-report=html

# Integration tests only
pytest tests/integration/
```

## 📚 Documentation

### Adding Documentation

New features should include:
1. Code documentation (docstrings/comments)
2. User-facing documentation in `website/docs/`
3. Update to README.md if applicable
4. Example usage in appropriate guide

### Building Documentation Locally

```bash
cd website
npm install
npm start
```

Documentation will be available at `http://localhost:3000/Hephaestus/`

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow the Code of Conduct (when added)

## 🐛 Common Issues

### Tests Failing

- Ensure Qdrant is running: `docker ps`
- Check database is initialized: `ls hephaestus.db`
- Verify API keys in `.env` for integration tests

### Import Errors

- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Issues

- Clear node_modules: `rm -rf node_modules && npm install`
- Check ports: Make sure 3000 and 8000 are available

## 💡 Areas We Need Help

- **Documentation**: Improving guides and examples
- **Testing**: Increasing test coverage
- **Bug Fixes**: Check open issues labeled `good first issue`
- **Performance**: Optimizing agent coordination
- **Features**: See issues labeled `enhancement`

## 📞 Questions?

- Open a **Question** issue
- Check existing [GitHub Discussions](https://github.com/Ido-Levi/Hephaestus/discussions)
- Review the [documentation](https://ido-levi.github.io/Hephaestus/)

## 🎉 Thank You!

Every contribution helps make Hephaestus better. We appreciate your time and effort!
