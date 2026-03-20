# Contributing to WSPR-beacon
Thank you for your interest in contributing to the WSPR-beacon project! This document provides guidelines and instructions for contributing. Please read it carefully before submitting issues or pull requests.

## Table of contents
- [Code of conduct](#code-of-conduct)
- [Opening an issue](#opening-an-issue)
- [Feature requests](#feature-requests)
- [Setting up the development environment](#setting-up-the-development-environment)
- [Branch naming convention](#branch-naming-convention)
- [Making changes](#making-changes)
- [Submitting pull requests](#submitting-pull-requests)
- [Code review](#code-review)
- [Documentation contributions](#documentation-contributions)
- [Licensing](#licensing)

## Code of conduct
Be respectful, constructive, and professional in all interactions. We are committed to providing a welcoming environment for everyone. Harassment, offensive language, and unconstructive criticism are not tolerated.

## Opening an issue
The [GitHub Issues](https://github.com/IgrikXD/WSPR-beacon/issues) section is used for reporting bugs and requesting new features. Before creating a new issue, please:

1. **Use the latest version.** Make sure you are using the latest version of the project. The issue you are experiencing may have already been fixed in a newer release.
2. **Check existing issues.** Search through the [open](https://github.com/IgrikXD/WSPR-beacon/issues) and [closed](https://github.com/IgrikXD/WSPR-beacon/issues?q=is%3Aissue+is%3Aclosed) issues to ensure your problem has not already been reported.
3. **Add information to existing issues.** If an issue matching your problem already exists, add a comment with any additional information you have rather than creating a duplicate.

When creating a new bug report, include:
- A clear and descriptive title.
- Steps to reproduce the problem.
- Expected behavior vs. actual behavior.
- Environment details (_operating system, Python version, device revision, firmware version, BEACON.App version_).
- Relevant screenshots, logs or error messages.

> [!WARNING]
> Do not paste large logs directly into the issue body or comments - this clutters the issue and makes it difficult to analyze. Upload full log output to [GitHub Gist](https://gist.github.com/) and include the link instead. Only short, isolated snippets demonstrating a specific behavior are acceptable to include directly in the issue.

## Feature requests
You are welcome to submit feature requests through [GitHub Issues](https://github.com/IgrikXD/WSPR-beacon/issues). When proposing a new feature:

- Clearly describe the feature and the problem it solves.
- Explain your use case and why this feature would be useful.
- Provide examples or references to similar implementations in other projects if applicable.

> [!NOTE]
> All feature requests will be reviewed, but their inclusion is not guaranteed - particularly if the proposed functionality falls outside the project's scope. No commitments are made regarding the implementation timeline or the release of any specific feature. The decision to implement and release requested functionality is at the discretion of the project developer.

## Setting up the development environment
- **BEACON.App:** For instructions on setting up the development environment, installing dependencies, building the application, and running tests, refer to the [BEACON.App README](./App/README.md).
- **ATmega328P firmware:** For instructions on building the firmware, refer to the [ATmega328P firmware README](./Firmware/ATmega328P-based/README.md).

> [!IMPORTANT]
> The ESP32-C3 firmware is proprietary and its source code is not publicly available. Code contributions to the ESP32-C3 firmware are not accepted. However, you are welcome to submit feature requests and bug reports through [GitHub Issues](https://github.com/IgrikXD/WSPR-beacon/issues).

## Branch naming convention
Use the following prefixes when creating branches to clearly indicate the scope of your changes:

| Prefix       | Scope                                       | Example                               |
|--------------|---------------------------------------------|---------------------------------------|
| `app/`       | Changes to BEACON.App (`App/`)              | `app/fix-serial-timeout`              |
| `firmware/`  | Changes to firmware (`Firmware/`)           | `firmware/add-gps-retry-logic`        |
| `pcb/`       | Changes to PCB files (`PCB/`)               | `pcb/update-bom-for-rev-3.3`         |
| `docs/`      | Root-level documentation and `Resources/`   | `docs/update-usage-guide`             |
| `ci/`        | GitHub Actions and CI/CD configuration      | `ci/add-lint-workflow`                |
| `copilot/`   | GitHub Copilot configuration modifications  | `copilot/update-python-instructions`  |

Always branch from the latest `master` branch and keep your branch up to date by rebasing before submitting a pull request.

> [!NOTE]
> The `docs/` scope applies to root-level documentation files and the `Resources/` directory. Documentation changes within `App/`, `Firmware/`, or `PCB/` should use the corresponding component prefix (_`app/`, `firmware/`, `pcb/`_).

## Making changes

### General guidelines
- **One PR per change.** Each pull request should contain isolated changes related to a single bug fix or a single new feature. Do not combine unrelated changes.
- **Write clear code.** Aim for code that is unambiguous and easy to understand. If a piece of logic is complex or non-obvious, add comments to explain it.

### BEACON.App
- **Follow PEP 8.** Consistency with the existing codebase is required. Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code formatting, use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for documentation, and refer to the existing codebase for naming conventions and project-specific patterns.
- **Write tests.** Any new functionality must be covered by unit tests. Features that involve hardware interaction must also be covered by integration tests. Use **pytest** as the test framework, and mark tests with `@pytest.mark.unit` or `@pytest.mark.integration` accordingly.
- **Use linting tools.** Run `flake8` before committing to ensure your code passes all lint checks. The project's flake8 configuration is defined in `App/.flake8`.

### ATmega328P-based firmware
- **Follow the existing code style.** Use `UPPER_CASE` for constants and `#define` macros, `camelCase` for variables and functions. Use 4-space indentation. Refer to the existing `.ino` files for naming conventions and project-specific patterns.
- **Keep user-configurable parameters at the top.** All `#define` values that end users may need to modify (_call sign, frequency band, calibration factor, etc._) must be placed in the configuration section at the top of the `.ino` file.

### Commit messages
Write clear, concise commit messages that describe _what_ was changed and _why_. Use the imperative mood (_e.g., "Fix serial timeout handling" instead of "Fixed serial timeout handling"_).

## Submitting pull requests

### PR title format
The pull request title **must** include a scope prefix indicating the area of the project affected by the changes:

| Prefix               | Scope                                      | Example                                                        |
|----------------------|--------------------------------------------|----------------------------------------------------------------|
| `[App]`              | Changes to BEACON.App                      | `[App] Fix WebSocket reconnection handling on connection timeout` |
| `[Firmware]`         | Changes to firmware                        | `[Firmware] Add GPS module retry logic for cold start conditions` |
| `[PCB]`              | Changes to PCB files                       | `[PCB] Update BOM for revision 3.3`                            |
| `[Docs]`             | Root-level documentation and `Resources/`  | `[Docs] Update ESP32-C3 firmware installation guide`           |
| `[GitHub Actions]`   | CI/CD workflow changes                     | `[GitHub Actions] Add Python lint check to the test workflow`  |
| `[Copilot]`          | GitHub Copilot configuration changes       | `[Copilot] Update Python coding conventions in instructions`   |

> [!NOTE]
> The `[Docs]` scope applies to root-level documentation files and the `Resources/` directory. Documentation changes within `App/`, `Firmware/`, or `PCB/` should use the corresponding component prefix (_`[App]`, `[Firmware]`, `[PCB]`_).

### PR description
The pull request description must include:
- A detailed explanation of the changes being introduced.
- The motivation or context behind the changes (_reference the related issue if applicable_).
- Test results (_if applicable_).
- Any relevant screenshots.

> [!WARNING]
> Do not paste full test execution logs into the PR description or comments - this clutters the pull request and makes it difficult to review. Upload complete logs to [GitHub Gist](https://gist.github.com/) and include the link instead. Only short, isolated log snippets that demonstrate a specific behavior are acceptable to include directly in the PR.

### PR labels
Apply appropriate [GitHub Labels](https://github.com/IgrikXD/WSPR-beacon/labels) to your pull request to categorize the changes. Labels help maintainers quickly understand the nature and scope of the proposed changes.

### PR requirements
- **No merge conflicts.** Pull requests containing merge conflicts will not be reviewed. Rebase your branch on the latest `master` and resolve any conflicts before submitting.
- **Passing CI checks.** All GitHub Actions checks must pass before the pull request can be reviewed.

## Code review
All pull requests go through a code review before being merged. During the review process:

- A maintainer will review your changes for correctness, code style adherence, and overall quality.
- You may be asked to make modifications, clarify implementation decisions, or add additional tests.
- Please respond to review feedback in a timely and constructive manner.
- Once all review comments are resolved and CI checks pass, the pull request will be merged by a maintainer.

> [!TIP]
> To streamline the review process, ensure your pull request follows all the guidelines described above, is well-tested, and contains a clear description of the changes.

## Documentation contributions
When modifying existing documentation or adding new documents:

- Use GitHub-flavored Markdown syntax.
- Wrap code examples and console output in fenced code blocks with proper language identifiers for syntax highlighting:
  ````markdown
  ```python
  def example():
      return "Hello, World!"
  ```
  ````
  ````markdown
  ```bash
  python -m pytest --cov=beaconapp --cov-config=pytest.ini
  ```
  ````
- Use [GitHub Alerts](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts) (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`) for important callouts.
- Ensure all links are valid and point to the correct targets.

## Licensing
By submitting a contribution, you agree that your work will be licensed under the terms described in the project's [licensing & terms of use](./DISCLAIMER.md).
