---
name: Feature Request
description: Suggest an idea for socialseed-e2e
title: "[Feature]: "
labels: ["enhancement", "triage"]
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to suggest a new feature! We appreciate your ideas and feedback to make socialseed-e2e better.

  - type: textarea
    id: problem
    attributes:
      label: Problem Description
      description: Is your feature request related to a problem? Please describe.
      placeholder: |
        A clear and concise description of what the problem is.

        Example: I'm always frustrated when [...]
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: Describe the solution you'd like to see
      placeholder: |
        A clear and concise description of what you want to happen.

        Example: Add a new CLI command `e2e generate-report` that creates HTML reports...
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: Describe any alternative solutions or features you've considered
      placeholder: |
        A clear and concise description of any alternative solutions or features you've considered.

        Example: I thought about using pytest-html plugin, but native integration would be better...
    validations:
      required: false

  - type: textarea
    id: use_case
    attributes:
      label: Use Case / User Story
      description: Describe the scenario where this feature would be helpful
      placeholder: |
        As a [type of user], I want [goal] so that [benefit].

        Example: As a QA engineer, I want to run tests in parallel so that my CI pipeline runs faster.
    validations:
      required: false

  - type: textarea
    id: examples
    attributes:
      label: Examples
      description: Provide examples of how this feature would be used
      placeholder: |
        ```python
        # Example code showing how the feature would work
        from socialseed_e2e import BasePage

        # Your example here
        ```

        Or command examples:
        ```bash
        $ e2e run --parallel 4
        ```
      render: markdown
    validations:
      required: false

  - type: dropdown
    id: priority
    attributes:
      label: Priority
      description: How important is this feature to you?
      options:
        - Nice to have
        - Would make my life easier
        - Major improvement
        - Critical for my workflow
      default: 1
    validations:
      required: false

  - type: checkboxes
    id: willingness
    attributes:
      label: Contribution
      description: Would you be willing to contribute this feature?
      options:
        - label: Yes, I'd be willing to submit a PR for this feature
          required: false
        - label: I can help test the feature
          required: false
        - label: I can provide more detailed specifications
          required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context, screenshots, or mockups about the feature request
      placeholder: |
        Any additional information, screenshots, or mockups that help explain your feature request.

        You can drag and drop images here.
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
