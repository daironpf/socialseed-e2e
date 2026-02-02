---
name: Bug Report
description: Create a report to help us improve socialseed-e2e
title: "[Bug]: "
labels: ["bug", "triage"]
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report! Please provide as much detail as possible to help us diagnose and fix the issue quickly.

  - type: textarea
    id: description
    attributes:
      label: Bug Description
      description: A clear and concise description of what the bug is.
      placeholder: Describe the bug you encountered...
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: Steps to reproduce the behavior
      placeholder: |
        1. Initialize project with 'e2e init test-project'
        2. Create service with 'e2e new-service test-api'
        3. Run 'e2e run'
        4. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What you expected to happen
      placeholder: Describe what you expected to happen...
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happened
      placeholder: Describe what actually happened, including any error messages...
    validations:
      required: true

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots or Logs
      description: If applicable, add screenshots or terminal output to help explain your problem
      placeholder: Paste screenshots or logs here...
    validations:
      required: false

  - type: markdown
    attributes:
      value: |
        ## Environment
        Please provide details about your environment:

  - type: input
    id: os
    attributes:
      label: Operating System
      description: What OS are you using?
      placeholder: e.g., Ubuntu 22.04, macOS 14, Windows 11
    validations:
      required: true

  - type: input
    id: python_version
    attributes:
      label: Python Version
      description: What version of Python are you using?
      placeholder: e.g., 3.11.4
    validations:
      required: true

  - type: input
    id: package_version
    attributes:
      label: socialseed-e2e Version
      description: What version of socialseed-e2e are you using?
      placeholder: e.g., 0.1.0
    validations:
      required: true

  - type: input
    id: playwright_version
    attributes:
      label: Playwright Version
      description: What version of Playwright are you using?
      placeholder: e.g., 1.40.0
    validations:
      required: false

  - type: textarea
    id: config
    attributes:
      label: Configuration File
      description: If applicable, share your e2e.conf configuration (remove sensitive data)
      placeholder: |
        ```yaml
        # Paste your e2e.conf here
        ```
      render: yaml
    validations:
      required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context about the problem here
      placeholder: Any additional information...
    validations:
      required: false

  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      description: By submitting this issue, you agree to follow our [Code of Conduct](https://github.com/daironpf/socialseed-e2e/blob/main/CODE_OF_CONDUCT.md)
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true
