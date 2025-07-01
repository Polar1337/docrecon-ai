# Contributing to DocRecon AI

Thank you for your interest in contributing to DocRecon AI! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Process](#contributing-process)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation](#documentation)
8. [Issue Reporting](#issue-reporting)
9. [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of document processing and NLP concepts

### Areas for Contribution

We welcome contributions in the following areas:

- **Core Features**: Crawler implementations, detection algorithms, reporting formats
- **Documentation**: User guides, API documentation, tutorials
- **Testing**: Unit tests, integration tests, performance tests
- **Performance**: Optimization, memory management, parallel processing
- **UI/UX**: Dashboard improvements, report visualizations
- **Integrations**: New storage systems, cloud services, APIs

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/docrecon-ai.git
cd docrecon-ai
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Verify Installation

```bash
# Run tests to ensure everything works
pytest tests/

# Run the CLI to verify installation
python -m docrecon_ai --help
```

## Contributing Process

### 1. Create an Issue

Before starting work, create an issue to discuss:
- Bug reports with reproduction steps
- Feature requests with use cases
- Documentation improvements
- Performance optimizations

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

### 3. Make Changes

Follow the coding standards and include tests for new functionality.

### 4. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration

# Check code coverage
pytest --cov=src/docrecon_ai --cov-report=html
```

### 5. Submit Pull Request

Create a pull request with a clear description of your changes.

## Coding Standards

### Python Style

We follow PEP 8 with some additional conventions:

```python
# Use type hints
def process_documents(documents: List[DocumentInfo]) -> Dict[str, Any]:
    """Process documents and return results."""
    pass

# Use descriptive variable names
document_count = len(documents)
similarity_threshold = 0.8

# Use docstrings for all public functions
def calculate_similarity(doc1: DocumentInfo, doc2: DocumentInfo) -> float:
    """
    Calculate semantic similarity between two documents.
    
    Args:
        doc1: First document
        doc2: Second document
        
    Returns:
        Similarity score between 0 and 1
    """
    pass
```

### Code Formatting

We use automated tools for consistent formatting:

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check style with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/docrecon_ai/
```

### Error Handling

Use consistent error handling patterns:

```python
import logging

logger = logging.getLogger(__name__)

def risky_operation(data: Any) -> Optional[Result]:
    """Perform operation that might fail."""
    try:
        # Operation logic
        return result
    except SpecificException as e:
        logger.error(f"Specific error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ProcessingError(f"Operation failed: {e}")
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interaction
├── fixtures/       # Test data and fixtures
└── conftest.py     # Shared test configuration
```

### Writing Tests

```python
import pytest
from src.docrecon_ai.module import ClassToTest

class TestClassToTest:
    """Test cases for ClassToTest."""
    
    def test_normal_operation(self, sample_data):
        """Test normal operation with valid input."""
        instance = ClassToTest()
        result = instance.method(sample_data)
        assert result.is_valid()
        
    def test_edge_case(self):
        """Test edge case handling."""
        instance = ClassToTest()
        result = instance.method(edge_case_input)
        assert result == expected_edge_result
        
    def test_error_handling(self):
        """Test error handling with invalid input."""
        instance = ClassToTest()
        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

### Test Coverage

- Aim for at least 80% code coverage
- Focus on critical paths and edge cases
- Include both positive and negative test cases
- Test error conditions and recovery

## Documentation

### Code Documentation

- Use clear, descriptive docstrings
- Include type hints for all parameters
- Document complex algorithms and business logic
- Provide usage examples for public APIs

### User Documentation

- Update user guides for new features
- Include configuration examples
- Provide troubleshooting information
- Add screenshots for UI changes

### API Documentation

- Document all public classes and methods
- Include parameter descriptions and return values
- Provide code examples
- Document exceptions that may be raised

## Issue Reporting

### Bug Reports

Include the following information:

```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- DocRecon AI version: [e.g., 1.0.0]

**Additional Context**
- Configuration files (remove sensitive data)
- Log files
- Screenshots if applicable
```

### Feature Requests

Include the following information:

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Any other relevant information
```

## Pull Request Process

### Before Submitting

1. **Update Documentation**: Ensure all documentation is updated
2. **Add Tests**: Include tests for new functionality
3. **Run Tests**: Verify all tests pass locally
4. **Check Style**: Run linting tools and fix issues
5. **Update Changelog**: Add entry for significant changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review code and provide feedback
3. **Discussion**: Address feedback and make necessary changes
4. **Approval**: Once approved, changes are merged

### Merge Requirements

- All CI checks must pass
- At least one maintainer approval
- No unresolved review comments
- Up-to-date with main branch

## Development Workflow

### Branching Strategy

- `main`: Stable release branch
- `develop`: Development integration branch
- `feature/*`: Feature development branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Critical fixes for production

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(crawler): add SharePoint Online support
fix(detection): resolve hash calculation error
docs(readme): update installation instructions
test(nlp): add embedding generation tests
```

### Release Process

1. **Version Bump**: Update version numbers
2. **Changelog**: Update CHANGELOG.md
3. **Testing**: Run full test suite
4. **Documentation**: Update documentation
5. **Release**: Create GitHub release with notes

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussion
- **Documentation**: Comprehensive guides and API reference

### Maintainer Contact

For sensitive issues or questions, contact the maintainers directly through GitHub.

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributor statistics

Thank you for contributing to DocRecon AI! Your efforts help make document management more efficient for everyone.

