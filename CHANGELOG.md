# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Auto-detect ports from Dockerfile, application.yml, docker-compose.yml
- Try multiple detected ports until one connects successfully

### Fixed
- Port detection from source code scanning
- Service path resolution for port auto-detection

## [0.1.5] - 2026-02-17

### Added
- Modular CLI architecture with lazy loading
- 47 CLI commands with POO/SOLID patterns
- Comprehensive CLI documentation (cli-reference.md)
- MkDocs documentation configuration
- AWS CodePipeline CI/CD template

### Changed
- Refactored all commands into separate modules in commands/ package
- Lazy dependency installation per command
- Unified manifest location to .e2e/manifests/

### Fixed
- Recursion errors in analytics and visual testing
- Import errors in command modules
- Flask dependency in release workflow

## [0.1.4] - 2026-02-10

### Added
- 10 new modules for autonomous quality platform:
  - Visual Testing with AI comparison
  - gRPC Testing (advanced)
  - GraphQL Testing (advanced)
  - Assertions Library (enterprise)
  - Real-time Protocol Testing
  - Advanced Mocking Engine
  - Test Data Factory
  - Analytics Dashboard
  - Observability Integration
  - Distributed Testing

### Changed
- Demo APIs reorganized into structured folders (demos/)
- Demo REST API for immediate testing after e2e init

## [0.1.3] - 2026-02-05

### Added
- Deep Database Testing Enhancement (#017)
- Self-Healing Test Automation (#019)
- Advanced Chaos Engineering (#016)
- Comprehensive Security Testing Suite (#015)
- Enterprise-Grade CI/CD Pipeline Templates (#011)
- Performance Testing Suite
- Consumer-Driven Contract Testing

### Fixed
- Flask dependency for demo API
- PyPI verification issues

## [0.1.2] - 2026-01-30

### Added
- AI Project Manifest with JSON Knowledge Base (#188)
- Vector Embeddings & RAG for AI agents (#86)
- Zero-Config Deep Scan (#184)
- The Observer - Auto-detect running services and ports
- AI Discovery Report generation
- Autonomous Test Generation based on code intent

### Changed
- Improved port detection logic

## [0.1.1] - 2026-01-25

### Added
- Visual Traceability with Sequence Diagrams (#85)
- AI Regression Agents for Differential Testing (#84)
- AI-Driven Intelligent Fuzzing and Security Testing (#189)
- Record and Replay Test Sessions (#121)
- Comprehensive Assertion Library (#120)
- Advanced Test Organization with Tags and Dependencies (#119)

### Fixed
- Various test failures and linting issues

## [0.1.0] - 2026-02-01

### Added
- Initial release of socialseed-e2e
- Core framework with BasePage, ApiConfigLoader, TestOrchestrator
- CLI with commands: init, new-service, new-test, run, doctor, config
- Playwright integration for HTTP testing
- YAML/JSON configuration support
- Template system for scaffolding
- Mock API server for integration testing
- Rich CLI output with tables and progress bars
- Pytest integration with markers and coverage
- GitHub Actions CI/CD workflow
- Complete documentation suite

### Features
- Service-agnostic hexagonal architecture
- Automatic test discovery and execution
- Stateful test chaining with shared context
- Rate limiting and retry mechanisms
- Type-safe Pydantic models
- Environment variable support in configuration

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 0.1.5 | 2026-02-17 | Modular CLI, 47 commands, lazy loading |
| 0.1.4 | 2026-02-10 | 10 new modules, demo API |
| 0.1.3 | 2026-02-05 | Security, Chaos, Self-Healing |
| 0.1.2 | 2026-01-30 | AI Manifest, Deep Scan, RAG |
| 0.1.1 | 2026-01-25 | Visual Traceability, Fuzzing, Assertions |
| 0.1.0 | 2026-02-01 | Initial release |

---

## Migration Guides

### Upgrading from 0.1.x to 0.1.5

The CLI architecture changed significantly in 0.1.5:

1. Commands are now in separate modules under `src/socialseed_e2e/commands/`
2. Import patterns remain the same for end users
3. Run `e2e doctor` to verify installation

### Upgrading from 0.1.0 to 0.1.1

New features added:
- Test organization with tags requires updated module structure
- Run `e2e lint` to validate existing tests

[Unreleased]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/daironpf/socialseed-e2e/releases/tag/v0.1.0
