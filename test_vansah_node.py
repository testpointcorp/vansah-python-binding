"""
Full integration tests for the Vansah Python binding (VansahNode).

These tests talk to a real Vansah instance, so they are driven entirely by a
local `.env` file (copy `.env`, fill in real values). Every test is **skipped**
(not failed) when `VANSAH_TOKEN` is blank, so the suite is safe to run in CI
without credentials.

Run with:
    pip install requests pytest
    pytest -v test_vansah_node.py

Environment variables (see `.env`):
    VANSAH_URL, VANSAH_TOKEN, VANSAH_PROJECT_KEY, VANSAH_FOLDER_PATH,
    VANSAH_JIRA_ISSUE_KEY, VANSAH_TEST_CASE_KEY, VANSAH_ATP_KEY,
    VANSAH_ATP_ASSET_TYPE, VANSAH_STP_KEY, VANSAH_SPRINT_NAME,
    VANSAH_RELEASE_NAME, VANSAH_ENVIRONMENT_NAME, VANSAH_SCREENSHOT_PATH,
    VANSAH_DEBUG
"""
import base64
import os

import pytest

from VansahNode import VansahNode

# --------------------------------------------------------------------------- #
# .env loading (no external dependency)
# --------------------------------------------------------------------------- #


def _load_dotenv():
    """Minimal .env parser: KEY=VALUE lines, ignores comments/blank lines and
    strips surrounding quotes. Does not overwrite an already-set env var."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_dotenv()


def env(name, default=""):
    return os.environ.get(name, default)


# --------------------------------------------------------------------------- #
# Config pulled from the environment
# --------------------------------------------------------------------------- #

VANSAH_URL = env("VANSAH_URL", "https://prod.vansah.com")
VANSAH_TOKEN = env("VANSAH_TOKEN")
PROJECT_KEY = env("VANSAH_PROJECT_KEY")
FOLDER_PATH = env("VANSAH_FOLDER_PATH")
JIRA_ISSUE_KEY = env("VANSAH_JIRA_ISSUE_KEY")
TEST_CASE_KEY = env("VANSAH_TEST_CASE_KEY")
ATP_KEY = env("VANSAH_ATP_KEY")
ATP_ASSET_TYPE = env("VANSAH_ATP_ASSET_TYPE", "folder")
STP_KEY = env("VANSAH_STP_KEY")
SPRINT_NAME = env("VANSAH_SPRINT_NAME")
RELEASE_NAME = env("VANSAH_RELEASE_NAME")
ENVIRONMENT_NAME = env("VANSAH_ENVIRONMENT_NAME")
SCREENSHOT_PATH = env("VANSAH_SCREENSHOT_PATH")
DEBUG = env("VANSAH_DEBUG").lower() in ("1", "true", "yes")

# Skip the whole module when no token is configured.
pytestmark = pytest.mark.skipif(
    not VANSAH_TOKEN,
    reason="VANSAH_TOKEN is not set in the environment/.env; skipping live Vansah tests.",
)

# A tiny valid 1x1 PNG, used when no real screenshot path is configured.
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _screenshot_path(tmp_path):
    if SCREENSHOT_PATH and os.path.isfile(SCREENSHOT_PATH):
        return SCREENSHOT_PATH
    p = tmp_path / "placeholder.png"
    p.write_bytes(_TINY_PNG)
    return str(p)


@pytest.fixture
def vansah():
    """A configured VansahNode instance for each test."""
    v = VansahNode()
    v.set_vansah_url(VANSAH_URL)
    v.set_vansah_token(VANSAH_TOKEN)
    v.set_project_key(PROJECT_KEY)
    v.set_jira_issue_key(JIRA_ISSUE_KEY)
    v.set_test_folders_path(FOLDER_PATH)
    if SPRINT_NAME:
        v.set_sprint_name(SPRINT_NAME)
    if RELEASE_NAME:
        v.set_release_name(RELEASE_NAME)
    if ENVIRONMENT_NAME:
        v.set_environment_name(ENVIRONMENT_NAME)
    v.set_advanced_test_plan_key(ATP_KEY)
    v.set_standard_test_plan_key(STP_KEY)
    v.set_debug(DEBUG)
    return v


# --------------------------------------------------------------------------- #
# Pure-logic tests (do not require the network)
# --------------------------------------------------------------------------- #


def test_result_mapping():
    v = VansahNode()
    assert v.result_obj("passed") == {"id": 2}
    assert v.result_obj("FAILED") == {"id": 1}
    assert v.result_obj("na") == {"id": 0}
    assert v.result_obj("untested") == {"id": 3}
    assert v.result_obj(2) == {"id": 2}
    assert v.result_obj("unknown") == {"id": 0}


def test_folder_path_validation():
    v = VansahNode()
    assert v.is_valid_folder_path("regression/login/") is True
    assert v.is_valid_folder_path("/leading") is False
    assert v.is_valid_folder_path("nogap") is False
    assert v.is_valid_folder_path("") is False


def test_planned_run_and_plan_assets():
    v = VansahNode()
    v.set_test_plan_iteration(3)
    assert v.planned_run_asset("KAN-P17") == {
        "type": "plannedRun", "key": "KAN-P17", "iteration": 3,
    }
    v.set_test_folders_path("regression/login/")
    v.TEST_PLAN_ASSET_TYPE = "folder"
    assert v.test_plan_asset() == {"type": "folder", "folderPath": "regression/login/"}
    v.set_jira_issue_key("KAN-1")
    v.TEST_PLAN_ASSET_TYPE = "issue"
    assert v.test_plan_asset() == {"type": "issue", "key": "KAN-1"}


def test_iteration_out_of_range_ignored():
    v = VansahNode()
    v.set_test_plan_iteration(9)          # invalid -> ignored
    assert v.TEST_PLAN_ITERATION is None  # stays default (API sends 1)
    v.set_test_plan_iteration(4)
    assert v.TEST_PLAN_ITERATION == 4


# --------------------------------------------------------------------------- #
# Live integration tests
# --------------------------------------------------------------------------- #


def test_run_from_jira_issue_step_by_step(vansah):
    vansah.add_test_run_from_jira_issue(TEST_CASE_KEY)
    assert vansah.TEST_RUN_IDENTIFIER, "Run identifier was not set"

    for step in range(1, 3):
        vansah.add_test_log("passed", f"Step {step} from the Python binding", step)
        assert vansah.TEST_LOG_IDENTIFIER, f"Log identifier not set for step {step}"

    # Update the most recent log, then remove it (placeholder is recreated).
    vansah.update_test_log("failed", "Updated from the Python binding")
    vansah.remove_test_log()
    vansah.remove_test_run()


def test_run_from_test_folder_with_screenshot(vansah, tmp_path, capsys):
    vansah.add_test_run_from_test_folder(TEST_CASE_KEY)
    assert vansah.TEST_RUN_IDENTIFIER, "Run identifier was not set"

    shot = _screenshot_path(tmp_path)
    vansah.add_test_log("passed", "Step 1 with screenshot", 1, image_path=shot)
    assert vansah.TEST_LOG_IDENTIFIER, "Log identifier not set"

    # The screenshot is uploaded via POST /logs/<id>/attachments; confirm it was accepted.
    out = capsys.readouterr().out
    assert f"Screenshot attached to LOG ID: {vansah.TEST_LOG_IDENTIFIER}" in out, \
        "Attachment was not accepted by Vansah"

    vansah.remove_test_run()


def test_update_test_log_with_screenshot(vansah, tmp_path, capsys):
    vansah.add_test_run_from_test_folder(TEST_CASE_KEY)
    assert vansah.TEST_RUN_IDENTIFIER
    vansah.add_test_log("passed", "Step 1", 1)
    log_id = vansah.TEST_LOG_IDENTIFIER
    assert log_id

    shot = _screenshot_path(tmp_path)
    vansah.update_test_log("failed", "Re-checked, attaching evidence", image_path=shot)
    out = capsys.readouterr().out
    assert f"Screenshot attached to LOG ID: {log_id}" in out, \
        "Attachment on update was not accepted by Vansah"

    vansah.remove_test_run()


@pytest.mark.skipif(not STP_KEY, reason="VANSAH_STP_KEY not set")
def test_run_from_standard_test_plan(vansah):
    vansah.add_test_run_from_standard_test_plan(TEST_CASE_KEY)
    assert vansah.TEST_RUN_IDENTIFIER, "STP run identifier was not set"
    vansah.add_test_log("passed", "STP step 1 from the Python binding", 1)
    assert vansah.TEST_LOG_IDENTIFIER
    vansah.remove_test_run()


@pytest.mark.skipif(not ATP_KEY, reason="VANSAH_ATP_KEY not set")
def test_run_from_advanced_test_plan(vansah):
    vansah.add_test_run_from_advanced_test_plan(ATP_ASSET_TYPE, TEST_CASE_KEY)
    assert vansah.TEST_RUN_IDENTIFIER, "ATP run identifier was not set"
    vansah.add_test_log("passed", "ATP step 1 from the Python binding", 1)
    assert vansah.TEST_LOG_IDENTIFIER
    vansah.remove_test_run()


def test_quick_test_from_jira_issue(vansah):
    vansah.add_quick_test_from_jira_issue(TEST_CASE_KEY, "passed")
    assert vansah.TEST_RUN_IDENTIFIER, "Quick test run identifier was not set"
    vansah.remove_test_run()


def test_quick_test_from_test_folder(vansah):
    vansah.add_quick_test_from_test_folder(TEST_CASE_KEY, 2)
    assert vansah.TEST_RUN_IDENTIFIER, "Quick test run identifier was not set"
    vansah.remove_test_run()
