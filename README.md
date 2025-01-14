<div align="center">
   <a href="https://vansah.com"><img src="https://vansah.com/wp-content/uploads/2024/07/512x512-01-1.png" /></a><br>
</div>

<p align="center">The "Vansah API binding for Python" enables seamless integration with popular Python testing frameworks such as PyTest, Unittest, Behave, and Robot Framework, while efficiently sending test results to Vansah Test Management for Jira.</p>

<p align="center">
    <a href="https://vansah.com/"><b>Website</b></a> •
    <a href="https://vansah.com/connect-integrations/"><b>More Connect Integrations</b></a>
</p>

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Setup and Configuration](#setup-and-configuration)
  - [Prerequisites](#prerequisites)
  - [Basic Configuration](#basic-configuration)
- [Usage](#usage)
  - [1. Create a Test Run from Jira Issue](#1-create-a-test-run-from-jira-issue)
  - [2. Log Test Results](#2-log-test-results)
  - [3. Manage Test Artifacts](#3-manage-test-artifacts)
- [Use Case: Sending Test Results from Automation Framework to Vansah](#use-case-sending-test-results-from-automation-framework-to-vansah)
  - [Example: Integrating Selenium with Vansah](#example-integrating-selenium-with-vansah)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview
`VansahNode` is a Python library that allows you to interact with the Vansah Test Management system for Jira. This library helps automate the process of adding test runs, logging test results, and managing test artifacts in Vansah directly from your automation framework.

## Features
- Create test runs from Jira issues or test folders.
- Log test results for individual test steps.
- Attach screenshots or other artifacts to test logs.
- Manage test runs and logs programmatically.

---

## Installation
To get started with `VansahNode`, ensure you have Python 3.7+ installed. Then, install the required modules:

```bash
pip install requests
```

You can also install other dependencies (if applicable):

```bash
pip install -r requirements.txt
```

---

## Setup and Configuration
### Prerequisites
- **Vansah API Token**: Obtain your API token from the Vansah Test Management system.
- **Vansah URL**: The base URL for your Vansah instance (e.g., `https://prod.vansah.com`) or Obtain your Vansah Connect URL from Vansah Settings > Vansah API Tokens
.

### Basic Configuration
Set up your `VansahNode` instance by configuring the following:

1. **Vansah URL**
2. **Sprint, Environment, and Release details**
3. **API Token**
4. **Jira Issue Key or Test Folder ID**

Example:

```python
from VansahNode import VansahNode

# Initialize the VansahNode instance
vansahnode = VansahNode()

# Set up configuration
vansahnode.set_vansah_url("https://prod.vansah.com")
vansahnode.set_vansah_token("<YOUR_API_TOKEN>")
vansahnode.set_sprint_name("Sprint 1")
vansahnode.set_environment_name("UAT")
vansahnode.set_release_name("Release 1")
vansahnode.set_jira_issue_key("PROJECT-123")

#Add Project Key in case of Test Folder runs
vansahnode.set_project_key("PROJECT")
```

---

## Usage

### 1. Create a Test Run from Jira Issue
Use the `add_test_run_from_jira_issue` method to create a test run linked to a Jira issue.

```python
# Create a test run for a specific test case
TEST_CASE = "PROJECT-TC1"
vansahnode.add_test_run_from_jira_issue(TEST_CASE)
```

### 2. Log Test Results
Log results for specific test steps within a test run.

```python
# Log a test result with a screenshot
vansahnode.add_test_log(
    result="passed",  # Result: "passed", "failed", etc.
    comment="Test step executed successfully.",
    test_step_row=1,  # Step number
    image_path=r"path/to/screenshot.png"  # Optional screenshot
)
```

### 3. Manage Test Artifacts
- **Remove a Test Run**:

```python
vansahnode.remove_test_run()  # Requires TEST_RUN_IDENTIFIER to be set
```

- **Remove a Test Log**:

```python
vansahnode.remove_test_log()  # Requires TEST_LOG_IDENTIFIER to be set
```

---

## Use Case: Sending Test Results from Automation Framework to Vansah

### Example: Integrating Selenium with Vansah
Here’s how you can send test results from a Selenium test script to Vansah:

```python
from selenium import webdriver
from VansahNode import VansahNode

# Initialize VansahNode
vansahnode = VansahNode()
vansahnode.set_vansah_url("https://vtrunk.vansahnode.app")
vansahnode.set_vansah_token("<YOUR_API_TOKEN>")
vansahnode.set_sprint_name("Sprint 1")
vansahnode.set_environment_name("UAT")
vansahnode.set_release_name("Release 1")
vansahnode.set_jira_issue_key("PROJECT-123")

# Set up Selenium
driver = webdriver.Chrome()
try:
    driver.get("https://example.com")
    assert "Example Domain" in driver.title

    # Create a test run
    TEST_CASE = "PROJECT-TC1"
    vansahnode.add_test_run_from_jira_issue(TEST_CASE)

    # Log the result
    vansahnode.add_test_log(
        result="passed",
        comment="Homepage loaded successfully.",
        test_step_row=1,
        image_path="path/to/screenshot.png"
    )
except Exception as e:
    vansahnode.add_test_log(
        result="failed",
        comment=f"Test failed with error: {e}",
        test_step_row=1
    )
finally:
    driver.quit()
```

---

## Troubleshooting
1. **Error: `TEST_RUN_IDENTIFIER is not set`**
   - Ensure you call `add_test_run_from_jira_issue` or `add_test_run_from_test_folder` before logging test results.

2. **Error: Authentication Failed**
   - Verify your API token and Vansah URL.

3. **File Not Found Error**
   - Check the file path provided for screenshots or other artifacts.

---

## Contributing
We welcome contributions! Please feel free to submit issues or pull requests to improve this library.

---

## Developed By

[Vansah](https://vansah.com/)