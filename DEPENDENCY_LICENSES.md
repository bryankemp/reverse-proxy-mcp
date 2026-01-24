# Dependency License Analysis

## Project License
**Nginx Manager** is licensed under the **BSD 3-Clause License**

## Dependency License Compatibility

All dependencies are compatible with BSD 3-Clause. MIT and Apache 2.0 licenses are permissive and can be used in BSD 3-Clause projects.

### Core Dependencies

| Package | License | Compatibility |
|---------|---------|----------------|
| fastapi | MIT | ✓ Compatible |
| uvicorn | BSD | ✓ Compatible |
| sqlalchemy | MIT | ✓ Compatible |
| alembic | MIT | ✓ Compatible |
| pydantic | MIT | ✓ Compatible |
| pydantic-settings | MIT | ✓ Compatible |
| python-jose | MIT | ✓ Compatible |
| python-multipart | Apache 2.0 | ✓ Compatible |
| bcrypt | Apache 2.0 | ✓ Compatible |
| python-dotenv | BSD 3-Clause | ✓ Compatible |
| jinja2 | BSD 3-Clause | ✓ Compatible |
| requests | Apache 2.0 | ✓ Compatible |
| mcp | MIT | ✓ Compatible |
| cryptography | Apache 2.0 / BSD | ✓ Compatible |

### Development Dependencies

| Package | License | Compatibility |
|---------|---------|----------------|
| pytest | MIT | ✓ Compatible |
| pytest-cov | MIT | ✓ Compatible |
| pytest-asyncio | MIT | ✓ Compatible |
| pytest-mock | MIT | ✓ Compatible |
| black | MIT | ✓ Compatible |
| ruff | MIT | ✓ Compatible |
| mypy | MIT | ✓ Compatible |
| types-requests | Apache 2.0 | ✓ Compatible |
| pre-commit | MIT | ✓ Compatible |
| sphinx | BSD 2-Clause | ✓ Compatible |
| sphinx-rtd-theme | MIT | ✓ Compatible |
| myst-parser | MIT | ✓ Compatible |

## License Compatibility Summary

✓ **All dependencies are permissive and compatible with BSD 3-Clause**

- **MIT License**: Most restrictive of the compatible licenses. Allows commercial use, modification, and distribution with attribution.
- **Apache 2.0 License**: Permissive license with explicit patent grant. Compatible with BSD 3-Clause.
- **BSD Licenses**: All variants are compatible with each other.

## Distribution Requirements

When distributing Nginx Manager, ensure:
1. Include the BSD 3-Clause License text in LICENSE file ✓
2. Include copyright notices for all dependencies
3. Preserve all notices in source code and documentation

For commercial use or closed-source derivative works, consult with legal counsel regarding license compliance.

## Compliance Status
✓ **COMPLIANT** - Project may use BSD 3-Clause License for all code and derivatives.
