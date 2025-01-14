from http.client import responses

import requests
import base64
import json

class VansahNode:
    """
    A Python class for interacting with the Vansah API.
    Provides methods to add, update, and remove test runs and logs.
    """
    API_VERSION = "v1"
    VANSAH_URL = "https://prod.vansahnode.app"
    VANSAH_TOKEN = "Your Vansah Connect Token"
    updateVansah = "1"

    def __init__(self):
        """
        Initializes the VansahNode instance.
        """
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
        self.resultAsName = None

    @staticmethod
    def set_vansah_url(vansah_url):
        """
        Sets the base URL for the Vansah API.

        :param vansah_url: The base URL to set.
        """
        VansahNode.VANSAH_URL = vansah_url

    def set_vansah_token(self, vansah_token):
        """
        Sets the authentication token for the Vansah API.

        :param vansah_token: The token to set.
        """
        self.VANSAH_TOKEN = vansah_token

    def set_project_key(self, project_key):
        """
        Sets the project key in the Request.

        :param project_key: The token to set.
        """
        self.PROJECT_KEY = project_key


    def set_test_folders_path(self, testfolder_path):
        """
        Sets the test folder ID.

        :param testfolder_path: The test folder ID to set.
        """
        self.TESTFOLDER_PATH = testfolder_path

    def set_jira_issue_key(self, jira_issue_key):
        """
        Sets the JIRA issue key.

        :param jira_issue_key: The JIRA issue key to set.
        """
        self.JIRA_ISSUE_KEY = jira_issue_key

    def set_sprint_name(self, sprint_name):
        """
        Sets the sprint name.

        :param sprint_name: The sprint name to set.
        """
        self.SPRINT_NAME = sprint_name

    def set_release_name(self, release_name):
        """
        Sets the release name.

        :param release_name: The release name to set.
        """
        self.RELEASE_NAME = release_name

    def set_environment_name(self, environment_name):
        """
        Sets the environment name.

        :param environment_name: The environment name to set.
        """
        self.ENVIRONMENT_NAME = environment_name

    def encode_file_to_base64(self, file_path):
        """
        Encodes a file to a Base64 string.

        :param file_path: The path to the file to encode.
        :return: The Base64 string of the file.
        """
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding file to Base64: {e}")
            return None

    def properties(self):
        """
        Constructs the properties JSON object.

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
        Constructs the test case JSON object.

        :return: A dictionary with the test case key.
        """
        if self.CASE_KEY:
            return {"key": self.CASE_KEY}
        else:
            print("Please provide a valid TestCase Key")
            return {}

    def result_obj(self, result):
        """
        Constructs the result object.

        :param result: The result name.
        :return: A dictionary with the result name.
        """
        return {"name": result}

    def connect_to_vansah_rest(self, endpoint, method="POST", payload=None):
        """
        Sends a request to the Vansah REST API.

        :param endpoint: The API endpoint.
        :param method: The HTTP method (default is POST).
        :param payload: The request payload.
        :return: The response JSON.
        """
        if VansahNode.updateVansah == "1":
            try:
                self.headers = {
                    "Authorization": self.VANSAH_TOKEN,
                    "Content-Type": "application/json"
                }
                self.resultAsName = {
                    "NA": 0,
                    "FAILED": 1,
                    "PASSED": 2,
                    "UNTESTED": 3
                }
                url = f"{VansahNode.VANSAH_URL}/api/{VansahNode.API_VERSION}/{endpoint}"
                response = requests.request(method, url, headers=self.headers, json=payload)
                response_data = response.json()

                if response.status_code == 200 and response_data.get("success"):
                    if endpoint == "run" :
                        self.TEST_RUN_IDENTIFIER = response_data["data"].get("run", {}).get("identifier")
                    if endpoint == "logs" :
                        self.TEST_LOG_IDENTIFIER = response_data["data"].get("log", {}).get("identifier")
                    print(f"Request to {endpoint} successful: {response_data.get("message")}")
                    return response_data
                else:
                    print(f"Error from Vansah: {response_data.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"Error connecting to Vansah API: {e}")

    def add_test_run_from_jira_issue(self, testcase):
        """
        Adds a test run from a JIRA issue.

        :param testcase: The test case identifier.
        """
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": {"type": "issue", "key": self.JIRA_ISSUE_KEY},
            "properties": self.properties()
        }
        self.connect_to_vansah_rest("run", payload=payload)

    def add_test_log(self, result, comment, test_step_row, image_path=None):
        """
        Adds a test log.

        :param result: The result name (e.g., 0 = N/A, 1 = FAIL, 2 = PASS, 3 = Not tested).
        :param comment: The comment for the log.
        :param test_step_row: The test step row number.
        :param image_path: Optional path to an image for the log.
        """
        self.RESULT_KEY = result
        self.COMMENT = comment
        self.STEP_ORDER = test_step_row

        if image_path:
            self.FILE = self.encode_file_to_base64(image_path)
            self.SEND_SCREENSHOT = True

        payload = {
            "run": {"identifier": self.TEST_RUN_IDENTIFIER},
            "step": {"number": self.STEP_ORDER},
            "result": self.result_obj(self.RESULT_KEY),
            "actualResult": self.COMMENT
        }

        if self.SEND_SCREENSHOT:
            payload["attachments"] = [{
                "name": "screenshot",
                "extension": "png",
                "file": self.FILE
            }]
        self.connect_to_vansah_rest("logs", payload=payload)

    def add_test_run_from_test_folder(self, testcase):
        """
        Adds a test run from a test folder.

        :param testcase: The test case identifier.
        """
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": {"type": "folder", "folderPath": self.TESTFOLDER_PATH},
            "properties": self.properties(),
            "project": {"key": self.PROJECT_KEY}
        }
        self.connect_to_vansah_rest("run", payload=payload)

    def add_quick_test_from_jira_issue(self, testcase, result):
        """
        Adds a quick test from a JIRA issue.

        :param testcase: The test case identifier.
        :param result: The result name.
        """
        self.CASE_KEY = testcase
        self.RESULT_KEY = result
        payload = {
            "case": self.test_case(),
            "asset": {"type": "issue", "key": self.JIRA_ISSUE_KEY},
            "properties": self.properties(),
            "result": self.result_obj(self.RESULT_KEY)
        }
        self.connect_to_vansah_rest("run", payload=payload)

    def add_quick_test_from_test_folder(self, testcase, result):
        """
        Adds a quick test from a test folder.

        :param testcase: The test case identifier.
        :param result: The result name.
        """
        self.CASE_KEY = testcase
        self.RESULT_KEY = result
        payload = {
            "case": self.test_case(),
            "asset": {"type": "folder", "folderPath": self.TESTFOLDER_PATH},
            "properties": self.properties(),
            "result": self.result_obj(self.RESULT_KEY),
            "project":{"key":self.PROJECT_KEY}
        }
        self.connect_to_vansah_rest("run", payload=payload)

    def remove_test_run(self):
        """
        Removes a test run.
        """
        endpoint = f"run/{self.TEST_RUN_IDENTIFIER}"
        self.connect_to_vansah_rest(endpoint, method="DELETE")

    def remove_test_log(self):
        """
        Removes a test log.
        """
        endpoint = f"logs/{self.TEST_LOG_IDENTIFIER}"
        self.connect_to_vansah_rest(endpoint, method="DELETE")

    def update_test_log(self, result, comment, image_path=None):
        """
        Updates a test log.

        :param result: The updated result ID.
        :param comment: The updated comment.
        :param image_path: Optional path to an updated image.
        """
        self.RESULT_KEY = result
        self.COMMENT = comment

        if image_path:
            self.FILE = self.encode_file_to_base64(image_path)
            self.SEND_SCREENSHOT = True

        payload = {
            "result": self.result_obj(self.RESULT_KEY),
            "actualResult": self.COMMENT
        }

        if self.SEND_SCREENSHOT:
            payload["attachments"] = [{
                "name": "screenshot",
                "extension": "png",
                "file": self.FILE
            }]

        endpoint = f"logs/{self.TEST_LOG_IDENTIFIER}"
        self.connect_to_vansah_rest(endpoint, method="PUT", payload=payload)

    def test_step_count(self, case_key):
        """
        Retrieves the count of test steps for a given test case.

        :param case_key: The key of the test case.
        :return: The number of test steps.
        """
        try:
            endpoint = "testCase/list/testScripts"
            params = {"caseKey": case_key}
            url = f"{VansahNode.VANSAH_URL}/api/{VansahNode.API_VERSION}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    steps = response_data.get("data", {}).get("steps", [])
                    print(f"Number of steps: {len(steps)}")
                    return len(steps)
                else:
                    print(f"Error: {response_data.get('message', 'Unknown error')}")
            else:
                print(f"HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"Error retrieving test steps: {e}")
        return 0