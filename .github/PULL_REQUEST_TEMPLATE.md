# Pull Request

## Description
<!-- Provide a brief description of the changes in this PR -->

**What does this PR do?**

<!-- Explain the purpose of this PR -->

**Why is this change needed?**

<!-- Describe the problem this PR solves or the feature it adds -->

**Related Issue(s)**
<!-- Link to the related issue(s) using the format: Closes #123, Fixes #456 -->
Closes #

## Type of Change
<!-- Mark the relevant option with an [x] -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Code style/formatting (formatting, renaming, refactoring)
- [ ] ♻️ Code refactoring (non-functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test updates (adding or correcting tests)
- [ ] 🔧 Build/CI/CD changes
- [ ] Other (please describe):

## Changes Made
<!-- List the specific changes made in this PR -->

-
-
-

## Testing
<!-- Describe how you tested your changes -->

**Test Environment:**
- OS:
- Python version:
- socialseed-e2e version:

**Tests Performed:**
<!-- Mark all that apply with [x] -->

- [ ] Unit tests pass (`pytest -m unit`)
- [ ] Integration tests pass (`pytest -m integration`)
- [ ] All tests pass (`pytest`)
- [ ] Manual testing performed
- [ ] Tested on clean environment

**Test Commands Run:**
```bash
# Add the commands you ran to test
pytest
pytest -m unit
pytest --cov=socialseed_e2e
```

## Checklist
<!-- Ensure all items are completed before submitting -->

### Code Quality
- [ ] My code follows the project's style guidelines (black, isort, flake8)
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have run pre-commit hooks (`pre-commit run --all-files`)

### Testing
- [ ] I have added tests that prove my fix is effective or my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested edge cases and error scenarios
- [ ] Test coverage is maintained or improved

### Documentation
- [ ] I have made corresponding changes to the documentation
- [ ] I have updated the README.md if needed
- [ ] I have updated the CHANGELOG.md with my changes (under [Unreleased])
- [ ] I have added docstrings to new functions/classes
- [ ] My changes are documented inline with comments

### Compatibility
- [ ] My changes are backward compatible
- [ ] I have considered the impact on existing users
- [ ] Breaking changes are clearly marked in the CHANGELOG.md

## Screenshots / Output Examples
<!-- If applicable, add screenshots or output examples to help explain your changes -->

### Before:
```
<!-- Show the previous behavior/output if applicable -->
```

### After:
```
<!-- Show the new behavior/output -->
```

## Additional Notes
<!-- Any additional information that reviewers should know -->

-
-

## Reviewer Checklist (for maintainers)
<!-- Reviewers will complete this section -->

- [ ] Code follows project conventions
- [ ] Tests are adequate and pass
- [ ] Documentation is clear and complete
- [ ] No security vulnerabilities introduced
- [ ] Performance impact is acceptable
- [ ] Ready to merge

---

**Thank you for your contribution! 🌱**

<!--
Remember:
- Keep PRs focused and atomic (one feature/fix per PR)
- Write clear commit messages following conventional commits
- Link related issues with Closes/Fixes/Relates keywords
- Be responsive to reviewer feedback
-->
