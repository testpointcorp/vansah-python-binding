import requests
import base64
import json

class VansahNode:
    API_VERSION = "v1"
    VANSAH_URL = "https://prod.vansahnode.app"
    VANSAH_TOKEN = "Your Token Here"
    updateVansah = "1"

    def __init__(self, TESTFOLDERS_ID=None, JIRA_ISSUE_KEY=None):
        self.TESTFOLDERS_ID = TESTFOLDERS_ID
        self.JIRA_ISSUE_KEY = JIRA_ISSUE_KEY
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
        self.headers = {
            "Authorization": VansahNode.VANSAH_TOKEN,
            "Content-Type": "application/json"
        }
        self.resultAsName = {
            "NA": 0,
            "FAILED": 1,
            "PASSED": 2,
            "UNTESTED": 3
        }

    @staticmethod
    def set_vansah_url(vansah_url):
        VansahNode.VANSAH_URL = vansah_url

    @staticmethod
    def set_vansah_token(vansah_token):
        VansahNode.VANSAH_TOKEN = vansah_token

    def set_test_folders_id(self, TESTFOLDERS_ID):
        self.TESTFOLDERS_ID = TESTFOLDERS_ID

    def set_jira_issue_key(self, JIRA_ISSUE_KEY):
        self.JIRA_ISSUE_KEY = JIRA_ISSUE_KEY

    def set_sprint_name(self, SPRINT_NAME):
        self.SPRINT_NAME = SPRINT_NAME

    def set_release_name(self, RELEASE_NAME):
        self.RELEASE_NAME = RELEASE_NAME

    def set_environment_name(self, ENVIRONMENT_NAME):
        self.ENVIRONMENT_NAME = ENVIRONMENT_NAME

    def encode_file_to_base64(self, file_path):
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding file to Base64: {e}")
            return None

    def properties(self):
        properties = {}
        if self.SPRINT_NAME:
            properties["sprint"] = {"name": self.SPRINT_NAME}
        if self.RELEASE_NAME:
            properties["release"] = {"name": self.RELEASE_NAME}
        if self.ENVIRONMENT_NAME:
            properties["environment"] = {"name": self.ENVIRONMENT_NAME}
        return properties

    def test_case(self):
        if self.CASE_KEY:
            return {"key": self.CASE_KEY}
        else:
            print("Please provide a valid TestCase Key")
            return {}

    def result_obj(self, result):
        return {"id": result}

    def connect_to_vansah_rest(self, endpoint, method="POST", payload=None):
        if VansahNode.updateVansah == "1":
            try:
                url = f"{VansahNode.VANSAH_URL}/api/{VansahNode.API_VERSION}/{endpoint}"
                response = requests.request(method, url, headers=self.headers, json=payload)
                response_data = response.json()

                if response.status_code == 200 and response_data.get("success"):
                    print(f"Request to {endpoint} successful: {response_data}")
                    return response_data
                else:
                    print(f"Error from Vansah: {response_data.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"Error connecting to Vansah API: {e}")

    def add_test_run_from_jira_issue(self, testcase):
        self.CASE_KEY = testcase
        payload = {
            "case": self.test_case(),
            "asset": {"type": "issue", "key": self.JIRA_ISSUE_KEY},
            "properties": self.properties()
        }
        self.connect_to_vansah_rest("run", payload=payload)

    def add_test_log(self, result, comment, test_step_row, image_path=None):
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