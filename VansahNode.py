import os
import requests
import base64


class VansahNode:
    """
    A Python class for interacting with the Vansah API (v2).

    Provides methods to create test runs (from a Jira issue, a test folder, a
    Standard Test Plan, or an Advanced Test Plan), record step-by-step results,
    attach screenshots, run quick tests, and update or remove runs and logs.

    A run is created as ``UNTESTED`` so Vansah pre-creates one log per test step;
    :meth:`add_test_log` then updates the correct step log in place instead of
    creating duplicates.
    """

    # The API version used for the Vansah API calls.
    # v2 is REQUIRED for Vansah Connect tokens; the deprecated v1 path rejects them.
    API_VERSION = "v2"

    # The default base URL of the Vansah API.
    # Note: For Data Residency support you can set this to your region URL.
    # https://help.vansah.com/en/articles/10407923-vansah-api-connect-url
    DEFAULT_VANSAH_URL = "https://prod.vansah.com"
    VANSAH_URL = DEFAULT_VANSAH_URL

    VANSAH_TOKEN = "Your Vansah Connect Token"

    # "1" sends results to Vansah, "0" disables all outgoing calls.
    updateVansah = "1"

    # Result name -> numeric id mapping used by the Vansah API (v2 expects an id).
    RESULT_AS_NAME = {
        "NA": 0,
        "FAILED": 1,
        "PASSED": 2,
        "UNTESTED": 3,
    }

    # Creating a run as UNTESTED (id 3) makes Vansah pre-create one UNTESTED log
    # per step of the test case; those per-step logs are then updated by add_test_log.
    UNTESTED_RESULT_ID = 3

    def __init__(self):
        """Initializes the VansahNode instance."""
        self.TESTFOLDER_PATH = None
        self.JIRA_ISSUE_KEY = None
        self.PROJECT_KEY = None
        self.SPRINT_NAME = None
        self.CASE_KEY = None
        self.RELEASE_NAME = None
        self.ENVIRONMENT_NAME = None
        self.RESULT_KEY = None
        self.SEND_SCREENSHOT = False
        self.COMMENT = None
        self.STEP_ORDER = None
        self.TEST_RUN_IDENTIFIER = None
        self.TEST_LOG_IDENTIFIER = None
        self.FILE = None
        self.image = None
        self.headers = None

        # Test Plan configuration.
        self.STANDARD_TEST_PLAN_KEY = None
        self.ADVANCED_TEST_PLAN_KEY = None
        self.TEST_PLAN_ITERATION = None  # None -> API default (iteration 1)
        self.TEST_PLAN_ASSET_TYPE = None  # "folder" or "issue" (Advanced Test Plan)

        # Maps a 1-based step number to the identifier of its pre-created log for
        # the current run, so add_test_log updates the correct step log.
        self.step_log_identifiers = {}

        # Request-payload logging. Enabled automatically when VANSAH_DEBUG is
        # set to "true" or "1"; toggle at runtime with set_debug().
        self.DEBUG = os.environ.get("VANSAH_DEBUG", "").lower() in ("true", "1")

    # --------------------------------------------------------------------- #
    # Configuration setters
    # --------------------------------------------------------------------- #

    @staticmethod
    def set_vansah_url(vansah_url):
        """
        Sets the base URL for the Vansah API. Falls back to the default URL if
        a null/empty value is provided.

        :param vansah_url: The base URL to set.
        """
        if vansah_url and vansah_url.strip():
            VansahNode.VANSAH_URL = vansah_url.strip()
        else:
            VansahNode.VANSAH_URL = VansahNode.DEFAULT_VANSAH_URL
            print("⚠️ Invalid VANSAH_URL. Resetting to default:", VansahNode.VANSAH_URL)

    def set_vansah_token(self, vansah_token):
        """
        Sets the authentication token for the Vansah API.

        :param vansah_token: The Vansah Connect token to set.
        """
        self.VANSAH_TOKEN = vansah_token

    def set_project_key(self, project_key):
        """
        Sets the Space Key (the Jira project key) that scopes your test runs and
        logs. Required for the Vansah API v2 — it is sent as the top-level
        ``project`` object on every request.

        :param project_key: The Space Key / Jira project key (e.g., "DEMO").
        """
        if project_key and project_key.strip():
            self.PROJECT_KEY = project_key.strip()
        else:
            print("⚠️ Warning: Provided Space Key is null or empty. Value not updated.")

    def set_test_folders_path(self, testfolder_path):
        """
        Sets the Test Folder path used by :meth:`add_test_run_from_test_folder`
        (and by an Advanced Test Plan run whose requirement is a folder).

        :param testfolder_path: The test folder path (e.g., "regression/login/").
        """
        self.TESTFOLDER_PATH = testfolder_path

    def set_jira_issue_key(self, jira_issue_key):
        """
        Sets the JIRA issue key.

        :param jira_issue_key: The JIRA issue key to set.
        """
        self.JIRA_ISSUE_KEY = jira_issue_key

    def set_sprint_name(self, sprint_name):
        """Sets the sprint name."""
        self.SPRINT_NAME = sprint_name

    def set_release_name(self, release_name):
        """Sets the release name."""
        self.RELEASE_NAME = release_name

    def set_environment_name(self, environment_name):
        """Sets the environment name."""
        self.ENVIRONMENT_NAME = environment_name

    def set_standard_test_plan_key(self, test_plan_key):
        """
        Sets the Standard Test Plan key that
        :meth:`add_test_run_from_standard_test_plan` runs against (e.g., "DEMO-P9").
        A null/empty value is ignored with a warning.

        :param test_plan_key: The Standard Test Plan key.
        """
        if test_plan_key and test_plan_key.strip():
            self.STANDARD_TEST_PLAN_KEY = test_plan_key.strip()
        else:
            print("⚠️ Warning: Provided Standard Test Plan Key is null or empty. Value not updated.")

    def set_advanced_test_plan_key(self, test_plan_key):
        """
        Sets the Advanced Test Plan key that
        :meth:`add_test_run_from_advanced_test_plan` runs against (e.g., "DEMO-P8").
        A null/empty value is ignored with a warning.

        :param test_plan_key: The Advanced Test Plan key.
        """
        if test_plan_key and test_plan_key.strip():
            self.ADVANCED_TEST_PLAN_KEY = test_plan_key.strip()
        else:
            print("⚠️ Warning: Provided Advanced Test Plan Key is null or empty. Value not updated.")

    def set_test_plan_iteration(self, iteration):
        """
        Sets the iteration to target when running against a Standard or Advanced
        Test Plan. Optional — runs default to iteration 1. Only affects the two
        test-plan run methods, not issue or folder runs.

        :param iteration: The iteration to target. Valid range is 1-5; values
            outside it are ignored (a warning is printed and the default of 1 is kept).
        """
        if isinstance(iteration, int) and 1 <= iteration <= 5:
            self.TEST_PLAN_ITERATION = iteration
        else:
            print("⚠️ Warning: Test Plan iteration must be between 1 and 5. Keeping the default of 1.")

    def set_debug(self, debug):
        """
        Enables or disables request-payload logging. When enabled, the JSON body
        sent to Vansah is printed before each API call — useful for diagnosing a
        malformed folder path or a missing Space Key. The token is sent as a
        header and is never printed; screenshot attachments are omitted from the log.

        :param debug: True to log outgoing request payloads, False to disable.
        """
        self.DEBUG = bool(debug)

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def encode_file_to_base64(self, file_path):
        """
        Encodes a file to a Base64 string.

        :param file_path: The path to the file to encode.
        :return: The Base64 string of the file, or None on error.
        """
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding file to Base64: {e}")
            return None

    def is_valid_folder_path(self, folder_path):
        """
        Validates the Test Folder path:
        - It must not be null or empty.
        - It must not start with a forward slash (/).
        - It must contain at least one forward slash (/).

        :param folder_path: The test folder path to validate.
        :return: True if valid, otherwise False (a warning is printed).
        """
        if not folder_path:
            print("⚠️ Warning: Folder path cannot be null or empty.")
            return False
        if folder_path.startswith("/"):
            print("⚠️ Warning: Folder path should not start with '/'.")
            return False
        if "/" not in folder_path:
            print("⚠️ Warning: Folder path must contain at least one '/'.")
            return False
        return True

    def _validate_screenshot_file(self, image_path):
        """
        Validates a screenshot path. On success sets SEND_SCREENSHOT and encodes
        the file; on failure disables the screenshot for this call.

        :param image_path: Path to the screenshot file.
        """
        if image_path and os.path.isfile(image_path):
            self.FILE = self.encode_file_to_base64(image_path)
            self.image = image_path
            self.SEND_SCREENSHOT = self.FILE is not None
        else:
            self.SEND_SCREENSHOT = False
            print("The Screenshot file provided does not exist or is not a file.")

    def _resolve_result(self, result):
        """
        Accepts a result as either an int id (0=N/A, 1=Fail, 2=Pass, 3=Untested)
        or a case-insensitive name ("NA", "FAILED", "PASSED", "UNTESTED") and
        returns the numeric id. Unknown names default to 0 (N/A).

        :param result: The result as an int or a string.
        :return: The numeric result id.
        """
        if isinstance(result, int):
            return result
        return VansahNode.RESULT_AS_NAME.get(str(result).upper(), 0)

    def _emit_payload(self, endpoint, payload):
        """Prints an outgoing request payload when debug is enabled. Base64 file
        data in attachments is redacted so the log is not flooded."""
        if not self.DEBUG:
            return
        safe = payload
        try:
            if isinstance(payload, dict) and payload.get("attachments"):
                safe = dict(payload)
                safe["attachments"] = [
                    {**{k: v for k, v in a.items() if k != "file"},
                     "file": f"<base64 {len(a.get('file', '') or '')} chars>"}
                    for a in payload["attachments"]
                ]
        except Exception:
            safe = payload
        print(f"🐛 [DEBUG] Request to {endpoint}: {safe}")

    def properties(self):
        """
        Constructs the run properties (sprint, release, environment).

        :return: A dictionary of properties.
        """
        properties = {}
        if self.SPRINT_NAME:
            properties["sprint"] = {"name": self.SPRINT_NAME}
        if self.RELEASE_NAME:
            properties["release"] = {"name": self.RELEASE_NAME}
        if self.ENVIRONMENT_NAME:
            properties["environment"] = {"name": self.ENVIRONMENT_NAME}
        return properties

    def test_case(self):
        """
        Constructs the test case object.

        :return: A dictionary with the test case key.
        """
        if self.CASE_KEY:
            return {"key": self.CASE_KEY}
        print("Please provide a valid TestCase Key")
        return {}

    def project_asset(self):
        """
        Constructs the top-level project (Space Key) scope. Required for Vansah
        Connect tokens. Returns an empty dict when no project key is set.

        :return: A dictionary with the project key, or empty.
        """
        if self.PROJECT_KEY:
            return {"key": self.PROJECT_KEY}
        return {}

    def jira_issue_asset(self):
        """Constructs the Jira issue asset object."""
        if self.JIRA_ISSUE_KEY:
            return {"type": "issue", "key": self.JIRA_ISSUE_KEY}
        print("Please Provide Valid JIRA Issue Key")
        return {}

    def test_folder_asset(self):
        """Constructs the test folder asset object."""
        if self.TESTFOLDER_PATH:
            self.is_valid_folder_path(self.TESTFOLDER_PATH)
            return {"type": "folder", "folderPath": self.TESTFOLDER_PATH}
        print("Please Provide Valid TestFolder Path")
        return {}

    def planned_run_asset(self, test_plan_key):
        """
        Constructs the "plannedRun" asset used for Standard/Advanced Test Plan runs.

        :param test_plan_key: The Standard or Advanced Test Plan key.
        :return: A dictionary with the plannedRun type, key, and iteration.
        """
        if test_plan_key and len(test_plan_key) >= 2:
            return {
                "type": "plannedRun",
                "key": test_plan_key,
                "iteration": self.TEST_PLAN_ITERATION if self.TEST_PLAN_ITERATION else 1,
            }
        print("Please Provide a Valid Test Plan Key")
        return {}

    def test_plan_asset(self):
        """
        Constructs the requirement backing an Advanced Test Plan (a folder path
        or an issue key), based on TEST_PLAN_ASSET_TYPE.

        :return: A dictionary describing the requirement asset.
        """
        if str(self.TEST_PLAN_ASSET_TYPE).lower() == "issue":
            return {"type": "issue", "key": self.JIRA_ISSUE_KEY}
        # default: folder
        return {"type": "folder", "folderPath": self.TESTFOLDER_PATH}

    def result_obj(self, result):
        """
        Constructs the result object. The Vansah API v2 expects an id.

        :param result: The numeric result id.
        :return: A dictionary with the result id.
        """
        return {"id": self._resolve_result(result)}

    def add_attachment(self):
        """Constructs an attachment object from the current screenshot file."""
        base_name = os.path.basename(self.image or "screenshot.png")
        name, ext = os.path.splitext(base_name)
        return {
            "name": name or "screenshot",
            "extension": ext.lstrip(".") or "png",
            "file": self.FILE,
        }

    def _upload_attachment(self, log_identifier):
        """
        Uploads the current screenshot to a test log via the dedicated Vansah v2
        endpoint ``POST /logs/{identifier}/attachments``. In v2, attachments must
        be posted to this sub-resource; an ``attachments`` array embedded in the
        log create/update body is ignored.

        :param log_identifier: The test log to attach the screenshot to.
        """
        if not (self.SEND_SCREENSHOT and self.FILE and log_identifier):
            return
        payload = {"attachments": [self.add_attachment()]}
        endpoint = f"logs/{log_identifier}/attachments"
        response_data = self.connect_to_vansah_rest(endpoint, method="POST", payload=payload)
        if response_data and response_data.get("success"):
            print(f"Screenshot attached to LOG ID: {log_identifier}")

    # --------------------------------------------------------------------- #
    # Core request
    # --------------------------------------------------------------------- #

    def connect_to_vansah_rest(self, endpoint, method="POST", payload=None):
        """
        Sends a request to the Vansah REST API and returns the parsed response.

        :param endpoint: The API endpoint (relative to /api/<version>/).
        :param method: The HTTP method (default is POST).
        :param payload: The request payload.
        :return: The response JSON dict, or None.
        """
        if VansahNode.updateVansah != "1":
            print("Sending Test Results to Vansah TM for JIRA is Disabled")
            return None
        try:
            self.headers = {
                "Authorization": self.VANSAH_TOKEN,
                "Content-Type": "application/json",
            }
            url = f"{VansahNode.VANSAH_URL}/api/{VansahNode.API_VERSION}/{endpoint}"
            self._emit_payload(url, payload)
            response = requests.request(method, url, headers=self.headers, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("success"):
                return response_data
            print(f"Response From Vansah: {response_data.get('message', 'Unknown error')}")
            return response_data
        except Exception as e:
            print(f"Error connecting to Vansah API: {e}")
            return None

    def _create_test_run(self, operation, payload):
        """
        Sends a run-creation request, stores the run identifier and the per-step
        log identifiers Vansah pre-creates.

        :param operation: A human-readable label for the run type (for logging).
        :param payload: The request payload.
        """
        response_data = self.connect_to_vansah_rest("run", payload=payload)
        if response_data and response_data.get("success"):
            run = response_data.get("data", {}).get("run", {})
            self.TEST_RUN_IDENTIFIER = run.get("identifier")
            self._store_step_logs(run)
            print(f"{operation} created successfully. RUN ID: {self.TEST_RUN_IDENTIFIER}")

    def _store_step_logs(self, run):
        """
        Caches the pre-created UNTESTED logs from a run-creation response, keyed
        by 1-based step number. The create response exposes each log's step as
        ``step.number``.

        :param run: The "run" object from the response (data.run).
        """
        self.step_log_identifiers = {}
        for log in (run or {}).get("logs", []) or []:
            number = log.get("step", {}).get("number")
            identifier = log.get("identifier")
            if number is not None and identifier is not None:
                self.step_log_identifiers[int(number)] = identifier

    def _step_for_log(self, log_identifier):
        """Returns the step number mapped to the given log identifier, or None."""
        for step, identifier in self.step_log_identifiers.items():
            if identifier == log_identifier:
                return step
        return None

    # --------------------------------------------------------------------- #
    # Test runs
    # --------------------------------------------------------------------- #

    def add_test_run_from_jira_issue(self, testcase):
        """
        Starts a test run for a test case against a Jira work item (issue).
        The run is created Untested with an empty log for each step; call
        :meth:`add_test_log` to record the result of each step.

        :param testcase: The test case key (e.g., "DEMO-C50").
        """
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": self.jira_issue_asset(),
            "result": self.result_obj(VansahNode.UNTESTED_RESULT_ID),
        }
        if self.properties():
            payload["properties"] = self.properties()
        if self.project_asset():
            payload["project"] = self.project_asset()
        self._create_test_run("Test Run", payload)

    def add_test_run_from_test_folder(self, testcase):
        """
        Starts a test run for a test case against a test folder.
        The run is created Untested with an empty log for each step; call
        :meth:`add_test_log` to record the result of each step.

        :param testcase: The test case key (e.g., "DEMO-C50").
        """
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": self.test_folder_asset(),
            "result": self.result_obj(VansahNode.UNTESTED_RESULT_ID),
        }
        if self.properties():
            payload["properties"] = self.properties()
        if self.project_asset():
            payload["project"] = self.project_asset()
        self._create_test_run("Test Run", payload)

    def add_test_run_from_standard_test_plan(self, testcase):
        """
        Starts a test run for a test case under a Standard Test Plan. Set the plan
        key first with :meth:`set_standard_test_plan_key`; the run targets
        iteration 1 unless you call :meth:`set_test_plan_iteration`.

        :param testcase: The test case key (e.g., "DEMO-C50"). Must belong to the plan.
        """
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": self.planned_run_asset(self.STANDARD_TEST_PLAN_KEY),
            "result": self.result_obj(VansahNode.UNTESTED_RESULT_ID),
        }
        if self.properties():
            payload["properties"] = self.properties()
        if self.project_asset():
            payload["project"] = self.project_asset()
        self._create_test_run("Standard Test Plan Run", payload)

    def add_test_run_from_advanced_test_plan(self, test_plan_asset_type, testcase):
        """
        Starts a test run for a test case under an Advanced Test Plan. Set the plan
        key first with :meth:`set_advanced_test_plan_key`; the run targets
        iteration 1 unless you call :meth:`set_test_plan_iteration`. Because a case
        can sit under more than one requirement in an advanced plan, pass the
        requirement's asset type and set its matching key (folder path via
        :meth:`set_test_folders_path` for "folder", or Jira issue key via
        :meth:`set_jira_issue_key` for "issue").

        :param test_plan_asset_type: The requirement the case runs under: "folder" or "issue".
        :param testcase: The test case key (e.g., "DEMO-C50"). Must belong to the plan.
        """
        self.TEST_PLAN_ASSET_TYPE = test_plan_asset_type
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": self.planned_run_asset(self.ADVANCED_TEST_PLAN_KEY),
            "testPlanAsset": self.test_plan_asset(),
            "result": self.result_obj(VansahNode.UNTESTED_RESULT_ID),
        }
        if self.properties():
            payload["properties"] = self.properties()
        if self.project_asset():
            payload["project"] = self.project_asset()
        self._create_test_run("Advanced Test Plan Run", payload)

    # --------------------------------------------------------------------- #
    # Test logs (step-by-step)
    # --------------------------------------------------------------------- #

    def add_test_log(self, result, comment, test_step_row, image_path=None):
        """
        Records the result and actual outcome for a single step of the current
        test run. Call one of the ``add_test_run_*`` methods first.

        If the step has a pre-created (Untested) log, it is updated in place;
        otherwise a fresh log is created for that step.

        :param result: Step result as an int (0=N/A, 1=Fail, 2=Pass, 3=Untested)
            or a case-insensitive name ("passed", "failed", "na", "untested").
        :param comment: Actual result text shown against the step.
        :param test_step_row: 1-based step number within the test case.
        :param image_path: Optional path to a screenshot to attach.
        """
        self.RESULT_KEY = result
        self.COMMENT = comment
        self.STEP_ORDER = test_step_row
        self.SEND_SCREENSHOT = False
        if image_path:
            self._validate_screenshot_file(image_path)

        existing_log_id = self.step_log_identifiers.get(test_step_row)

        if existing_log_id:
            # A log for this step was pre-created (Untested) when the run was
            # created. Update it in place rather than posting a new one (which
            # Vansah rejects with "A Test Log already exists for provided Step.").
            payload = {
                "result": self.result_obj(self.RESULT_KEY),
                "actualResult": self.COMMENT,
            }
            endpoint = f"logs/{existing_log_id}"
            response_data = self.connect_to_vansah_rest(endpoint, method="PUT", payload=payload)
            if response_data and response_data.get("success"):
                self.TEST_LOG_IDENTIFIER = existing_log_id
                self.step_log_identifiers[test_step_row] = existing_log_id
                print(f"Test Log for step {test_step_row} recorded. LOG ID: {self.TEST_LOG_IDENTIFIER}")
                self._upload_attachment(self.TEST_LOG_IDENTIFIER)
        else:
            # Fallback: no pre-created log for this step -- create one.
            payload = {
                "run": {"identifier": self.TEST_RUN_IDENTIFIER},
                "step": {"number": self.STEP_ORDER},
                "result": self.result_obj(self.RESULT_KEY),
                "actualResult": self.COMMENT,
            }
            response_data = self.connect_to_vansah_rest("logs", payload=payload)
            if response_data and response_data.get("success"):
                self.TEST_LOG_IDENTIFIER = response_data.get("data", {}).get("log", {}).get("identifier")
                self.step_log_identifiers[test_step_row] = self.TEST_LOG_IDENTIFIER
                print(f"Test Log for step {test_step_row} recorded. LOG ID: {self.TEST_LOG_IDENTIFIER}")
                self._upload_attachment(self.TEST_LOG_IDENTIFIER)

    def update_test_log(self, result, comment, image_path=None):
        """
        Updates the most recently recorded test log with a new result, comment,
        and optionally a screenshot.

        :param result: Result as an int or a case-insensitive name.
        :param comment: The updated comment.
        :param image_path: Optional path to a screenshot to attach.
        """
        self.RESULT_KEY = result
        self.COMMENT = comment
        self.SEND_SCREENSHOT = False
        if image_path:
            self._validate_screenshot_file(image_path)

        payload = {
            "result": self.result_obj(self.RESULT_KEY),
            "actualResult": self.COMMENT,
        }

        endpoint = f"logs/{self.TEST_LOG_IDENTIFIER}"
        response_data = self.connect_to_vansah_rest(endpoint, method="PUT", payload=payload)
        if response_data and response_data.get("success"):
            print(f"Test Log updated successfully. LOG ID: {self.TEST_LOG_IDENTIFIER}")
            self._upload_attachment(self.TEST_LOG_IDENTIFIER)

    # --------------------------------------------------------------------- #
    # Quick tests
    # --------------------------------------------------------------------- #

    def add_quick_test_from_jira_issue(self, testcase, result):
        """
        Creates a run and records a single overall result in one call — useful
        when a test is pass/fail as a whole and has no steps to report individually.

        :param testcase: The test case key.
        :param result: The overall result as an int or a case-insensitive name.
        """
        self.CASE_KEY = testcase
        self.RESULT_KEY = result
        payload = {
            "case": self.test_case(),
            "asset": self.jira_issue_asset(),
            "result": self.result_obj(self.RESULT_KEY),
        }
        if self.properties():
            payload["properties"] = self.properties()
        if self.project_asset():
            payload["project"] = self.project_asset()
        response_data = self.connect_to_vansah_rest("run", payload=payload)
        if response_data and response_data.get("success"):
            self.TEST_RUN_IDENTIFIER = response_data.get("data", {}).get("run", {}).get("identifier")
            print(f"Quick Test: {response_data.get('message')}")

    def add_quick_test_from_test_folder(self, testcase, result):
        """
        Creates a run and records a single overall result in one call, against a
        test folder.

        :param testcase: The test case key.
        :param result: The overall result as an int or a case-insensitive name.
        """
        self.CASE_KEY = testcase
        self.RESULT_KEY = result
        payload = {
            "case": self.test_case(),
            "asset": self.test_folder_asset(),
            "result": self.result_obj(self.RESULT_KEY),
        }
        if self.properties():
            payload["properties"] = self.properties()
        if self.project_asset():
            payload["project"] = self.project_asset()
        response_data = self.connect_to_vansah_rest("run", payload=payload)
        if response_data and response_data.get("success"):
            self.TEST_RUN_IDENTIFIER = response_data.get("data", {}).get("run", {}).get("identifier")
            print(f"Quick Test: {response_data.get('message')}")

    # --------------------------------------------------------------------- #
    # Remove
    # --------------------------------------------------------------------- #

    def remove_test_run(self):
        """Removes the current test run."""
        endpoint = f"run/{self.TEST_RUN_IDENTIFIER}"
        response_data = self.connect_to_vansah_rest(endpoint, method="DELETE")
        if response_data and response_data.get("success"):
            print(f"Test Run removed successfully. RUN ID: {self.TEST_RUN_IDENTIFIER}")

    def remove_test_log(self):
        """
        Removes the current test log. After removal, the step keeps an Untested
        placeholder log so it can be recorded again later.
        """
        removed_log_id = self.TEST_LOG_IDENTIFIER
        endpoint = f"logs/{removed_log_id}"
        response_data = self.connect_to_vansah_rest(endpoint, method="DELETE")
        if response_data and response_data.get("success"):
            print(f"Test Log removed successfully. LOG ID: {removed_log_id}")
            removed_step = self._step_for_log(removed_log_id)
            if removed_step is not None:
                self.step_log_identifiers.pop(removed_step, None)
            self.TEST_LOG_IDENTIFIER = None
            if removed_step is not None:
                self._recreate_untested_step_log(removed_step)

    def _recreate_untested_step_log(self, step_number):
        """
        Posts a fresh Untested log for a step (used after a step's log is removed)
        and caches its new identifier, so the step keeps a placeholder that a later
        add_test_log can update.

        :param step_number: The step whose placeholder log should be recreated.
        """
        if not self.TEST_RUN_IDENTIFIER:
            return
        payload = {
            "run": {"identifier": self.TEST_RUN_IDENTIFIER},
            "step": {"number": step_number},
            "result": self.result_obj(VansahNode.UNTESTED_RESULT_ID),
            "actualResult": "",
        }
        response_data = self.connect_to_vansah_rest("logs", payload=payload)
        if response_data and response_data.get("success"):
            new_id = response_data.get("data", {}).get("log", {}).get("identifier")
            if new_id:
                self.step_log_identifiers[step_number] = new_id
