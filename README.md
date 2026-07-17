<div align="center">
   <a href="https://vansah.com"><img src="https://vansah.com/app/logo/vansahjira-logo.svg" /></a><br>
</div>

<p align="center">The "Vansah API binding for Python" enables seamless integration with popular Python testing frameworks such as PyTest, Unittest, Behave, and Robot Framework, while efficiently sending test results to Vansah Test Management for Jira.</p>

<p align="center">
    <a href="https://vansah.com/"><b>Website</b></a> •
    <a href="https://vansah.com/connect-integrations/"><b>More Connect Integrations</b></a>
</p>
<hr>

> ⚠️ **API Token Update Required**
>
> Existing Vansah Connect tokens must be regenerated to continue using integrations. All Connect-based integrations and bindings must use the Vansah API v2 endpoint (`<your-vansah-connect-url>/api/v2/`). **This binding already targets v2.**
>
> - Generate a new Vansah API token
> - Test your integrations to ensure continuity post-release
>
> In the meantime, for more details check out:
> - [Vansah for Jira — May 2026 Forge Release](https://help.vansah.com/en/articles/13298303-vansah-for-jira-may-2026)
> - [What's new in Vansah — Migration to Forge Platform](https://vansah.com/blog/whats-new-in-vansah-migration-to-forge-platform/)
>
> Questions? [Open an issue](../../issues) or reach out via the [Vansah Support Portal](https://vansahapp.atlassian.net/servicedesk/customer/portals).
<hr>

## Table of Contents
- [Features](#features)
- [Prerequisite](#prerequisite)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage examples](#usage-examples)
  - [Step-by-step execution against a Jira Issue](#step-by-step-execution-against-a-jira-issue)
  - [Folder Path, Advanced Test Plan (ATP), and Standard Test Plan (STP)](#folder-path-advanced-test-plan-atp-and-standard-test-plan-stp)
- [Methods Overview](#methods-overview)
- [Setter Methods of Vansah Binding](#setter-methods-of-vansah-binding)
- [Troubleshooting](#troubleshooting)
- [Developed By](#developed-by)

---

## Features

- Set a custom API URL and token for authentication.
- Easily connect your Python applications with `Vansah Test Management for Jira` to report test results and update test runs without manual intervention.
- Report results as a single overall verdict (Quick Test) or **step by step**, against a **Jira issue**, a **test folder**, a **Standard Test Plan**, or an **Advanced Test Plan**.
- Target a specific **Test Plan iteration** (1–5).
- Attach **screenshots** to test steps for more detailed reporting and analysis.
- Request-payload logging (`set_debug`) to troubleshoot integration issues; the token is sent as a header and is never printed.
- Detailed documentation and usage examples to help you get started quickly.

---

## Prerequisite

- Make sure that [`Vansah`](https://marketplace.atlassian.com/apps/1224250/vansah-test-management-for-jira?tab=overview&hosting=cloud) is installed in your Jira workspace.
- Generate a Vansah [`connect`](https://help.vansah.com/en/articles/9824979-generate-a-vansah-api-token-from-jira) token to authenticate with the Vansah APIs.
- [Python 3.8+](https://www.python.org/downloads/) installed for Windows, Linux, or macOS.
- The `requests` library (see [Installation](#installation)).

---

## Installation

Install the required module:

```bash
pip install requests
```

Or, if a `requirements.txt` is provided:

```bash
pip install -r requirements.txt
```

Then copy [`VansahNode.py`](/VansahNode.py) into your test project and import it:

```python
from VansahNode import VansahNode
```

---

## Configuration

Provide your Vansah [`connect`](https://help.vansah.com/en/articles/9824979-generate-a-vansah-api-token-from-jira) token. You have two options:

- Set it directly on the instance:

  ```python
  vansah = VansahNode()
  vansah.set_vansah_token("Add your Token here")

  # Optional: set a custom API URL (from Vansah Settings > Vansah API Tokens)
  vansah.set_vansah_url("https://<your-vansah-connect-url>")
  ```

- Or read it from an environment variable so it never lands in source control:

  ```python
  import os
  vansah = VansahNode()
  vansah.set_vansah_token(os.environ.get("VANSAH_TOKEN"))
  ```

A minimal configuration looks like:

```python
from VansahNode import VansahNode

vansah = VansahNode()
vansah.set_vansah_url("https://prod.vansah.com")
vansah.set_vansah_token("<YOUR_API_TOKEN>")
vansah.set_project_key("DEMO")          # Space Key (Jira project key) — required for API v2
vansah.set_jira_issue_key("DEMO-1")
vansah.set_test_folders_path("regression/login/")
vansah.set_sprint_name("Sprint 1")
vansah.set_environment_name("UAT")
vansah.set_release_name("Release 1")
```

---

## Usage examples

### Step-by-step execution against a Jira Issue

```python
from VansahNode import VansahNode

vansah = VansahNode()
vansah.set_vansah_token("<YOUR_API_TOKEN>")
vansah.set_project_key("DEMO")        # Space Key (Jira project key) — required for API v2
vansah.set_jira_issue_key("DEMO-1")   # the work item this run is reported against
vansah.set_environment_name("QA")

# Start a run for the test case (created Untested; results come from the step logs)
vansah.add_test_run_from_jira_issue("DEMO-C1")

# Log a result for each step of the test case
try:
    # add_test_log(result, comment, step_number, screenshot_path=optional)
    vansah.add_test_log("passed", "Step 1 executed successfully", 1)
    vansah.add_test_log("passed", "Step 2 executed successfully", 2)
except Exception as e:
    # Update the step with a failure and a screenshot when something goes wrong
    vansah.update_test_log("failed", f"Step failed: {e}", r"path/to/screenshot.png")
```

### Folder Path, Advanced Test Plan (ATP), and Standard Test Plan (STP)

```python
from VansahNode import VansahNode

vansah = VansahNode()
vansah.set_vansah_url("https://prod.vansah.com")
vansah.set_vansah_token("<YOUR_API_TOKEN>")
vansah.set_project_key("KAN")                       # Space Key (Jira project key)
vansah.set_test_folders_path("vansah test automation/regression 2025/")
vansah.set_advanced_test_plan_key("KAN-P17")        # Advanced Test Plan key
vansah.set_standard_test_plan_key("KAN-P18")        # Standard Test Plan key
# vansah.set_test_plan_iteration(2)                 # optional — defaults to iteration 1

TEST_CASE = "KAN-C17"

# Test folder
vansah.add_test_run_from_test_folder(TEST_CASE)
vansah.add_test_log("passed", "Actual result for the Test Step", 1)

# Advanced Test Plan (ATP) — asset type is "folder" or "issue"
vansah.add_test_run_from_advanced_test_plan("folder", TEST_CASE)
vansah.add_test_log("passed", "Actual result for the Test Step", 1)

# Standard Test Plan (STP)
vansah.add_test_run_from_standard_test_plan(TEST_CASE)
vansah.add_test_log("passed", "Actual result for the Test Step", 1)
```

---

## Methods Overview

The `VansahNode` class provides a comprehensive interface for interacting with Vansah Test Management for Jira directly from Python. Below is a description of its public methods.

### `add_test_run_from_jira_issue(testcase)`

Creates a new test run linked to a specific Jira issue (set via `set_jira_issue_key`). The run is created `Untested`, with a log pre-created for each step; record each step's result with `add_test_log`.

- **Parameters**:
  - `testcase`: The test case key (e.g., `"DEMO-C1"`).

### `add_test_run_from_test_folder(testcase)`

Creates a new test run against a test folder (set the folder path via `set_test_folders_path`). The run is created `Untested`, with a log pre-created for each step.

- **Parameters**:
  - `testcase`: The test case key (e.g., `"KAN-C17"`).

### `add_test_run_from_standard_test_plan(testcase)`

Creates a new test run under a Standard Test Plan. Set the plan key first with `set_standard_test_plan_key(...)`. The run targets **iteration 1** by default; call `set_test_plan_iteration(...)` (range 1–5) beforehand to target a different iteration.

- **Parameters**:
  - `testcase`: The test case key to execute under the plan (e.g., `"KAN-C17"`).

### `add_test_run_from_advanced_test_plan(test_plan_asset_type, testcase)`

Creates a new test run under an Advanced Test Plan. Set the plan key first with `set_advanced_test_plan_key(...)`. Because a case can sit under more than one requirement, pass the requirement's asset type and set its matching key. The run targets **iteration 1** by default; call `set_test_plan_iteration(...)` beforehand to change it.

- **Parameters**:
  - `test_plan_asset_type`: The requirement the case runs under — `"folder"` (uses `set_test_folders_path`) or `"issue"` (uses `set_jira_issue_key`).
  - `testcase`: The test case key to execute (e.g., `"KAN-C17"`).

### `add_test_log(result, comment, test_step_row, image_path=None)`

Records the result and actual outcome for a single step of the current test run. Call one of the `add_test_run_*` methods first.

- **Parameters**:
  - `result`: Step result — as a name (`"passed"`, `"failed"`, `"na"`, `"untested"` — case-insensitive) or a code (`2`, `1`, `0`, `3`).
  - `comment`: Actual result text shown against the step.
  - `test_step_row`: 1-based step number within the test case.
  - `image_path` *(optional)*: Path to an image file to attach as evidence.

### `update_test_log(result, comment, image_path=None)`

Updates the most recently recorded step log with a new result, comment, and optionally a screenshot.

### `add_quick_test_from_jira_issue(testcase, result)` and `add_quick_test_from_test_folder(testcase, result)`

Creates a run and records a single overall result in one call — useful when a test is pass/fail as a whole and has no steps to report individually.

- **Parameters**:
  - `testcase`: The test case key.
  - `result`: The overall result, as a name or a code.

### `remove_test_run()` and `remove_test_log()`

Deletes a previously created test run or the most recent test log. After a log is removed, the step keeps an `Untested` placeholder so it can be recorded again later.

---

## Setter Methods of Vansah Binding

Configure the test context before creating runs or logs.

### `set_vansah_token(vansah_token)`

Sets the Vansah Connect token used to authenticate every request. Read it from an environment variable to keep it out of source control.

### `set_vansah_url(vansah_url)`

Sets a custom Vansah API URL. Obtain your Vansah Connect URL from **Vansah Settings > Vansah API Tokens**. If not set, the binding uses its default host (`https://prod.vansah.com`).

### `set_project_key(project_key)`

Sets the **Space Key** (the Jira project key) that scopes your test runs and logs. This is **required for the Vansah API v2** — it is sent as the top-level `project` object on every request (e.g., `"KAN"`). A null/empty value is ignored with a warning.

### `set_test_folders_path(testfolder_path)`

Sets the **Test Folder path** used by `add_test_run_from_test_folder` (and by an Advanced Test Plan run when its requirement is a folder), e.g., `"regression/login/"`. The path must contain at least one `/` and must not start with `/`.

### `set_jira_issue_key(jira_issue_key)`

Sets the Jira issue key used by `add_test_run_from_jira_issue` (and by an Advanced Test Plan run when its requirement is an issue).

### `set_sprint_name(...)`, `set_release_name(...)`, `set_environment_name(...)`

Optional run properties — the sprint, release/version, and environment (e.g., `"SYS"`, `"UAT"`) recorded against the run.

### `set_standard_test_plan_key(test_plan_key)`

Sets the Standard Test Plan key that `add_test_run_from_standard_test_plan(...)` runs against (e.g., `"KAN-P18"`). A null/empty value is ignored with a warning.

### `set_advanced_test_plan_key(test_plan_key)`

Sets the Advanced Test Plan key that `add_test_run_from_advanced_test_plan(...)` runs against (e.g., `"KAN-P17"`). A null/empty value is ignored with a warning.

### `set_test_plan_iteration(iteration)`

Sets the **iteration** to target when creating a run from a Standard or Advanced Test Plan. This is **optional** — if you never call it, runs default to **iteration 1**. Only call it when recording results against a specific iteration.

- **Parameters**:
  - `iteration`: The iteration to target. Valid range is **1–5**. Values outside this range are ignored (a warning is printed and the default of 1 is kept).

> **Note:** The iteration applies only to `add_test_run_from_standard_test_plan(...)` and `add_test_run_from_advanced_test_plan(...)`. It has no effect on Jira-issue or test-folder runs.

### `set_debug(debug)`

Enables or disables **request-payload logging**. When enabled, the JSON body sent to Vansah is printed before each API call — useful for diagnosing a malformed folder path or a missing Space Key. The token is sent as a header and is never printed; screenshot attachments are omitted from the log. Debug logging is also enabled automatically when the `VANSAH_DEBUG` environment variable is set to `true` or `1`.

- **Parameters**:
  - `debug`: `True` to log outgoing request payloads, `False` to disable.

---

## Troubleshooting

1. **`TEST_RUN_IDENTIFIER is not set` / "Please start a test run before recording a step result"**
   - Ensure you call one of the `add_test_run_*` methods before logging test results.

2. **Authentication failed / `JWT claim did not contain the issuer (iss)`**
   - Regenerate your Vansah Connect token and confirm the binding is targeting **API v2** (it is by default). Verify your token and Vansah URL.

3. **`Failed to validate asset from request` (errorCode 1306)**
   - Check the folder path: it must not start with `/` and must contain at least one `/`. Enable `set_debug(True)` to inspect the outgoing payload.

4. **File Not Found for screenshots**
   - Check the file path provided for the screenshot. Invalid paths are skipped with a warning.

Turn on `set_debug(True)` (or set `VANSAH_DEBUG=1`) to print each outgoing request payload while diagnosing issues.

---

## Developed By

[Vansah](https://vansah.com/)
