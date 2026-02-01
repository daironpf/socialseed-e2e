# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive CLI reference documentation
- Sphinx documentation setup with autodoc
- ReadTheDocs configuration

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

[Unreleased]: https://github.com/daironpf/socialseed-e2e/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/daironpf/socialseed-e2e/releases/tag/v0.1.0
