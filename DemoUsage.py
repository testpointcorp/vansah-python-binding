from VansahNode import VansahNode

# Initialize VansahNode with configuration and test details

# JIRA Test Requirement details
JIRA_ISSUE_KEY = "TF-1"  # JIRA issue key associated with the test requirement

# Vansah Test Case details
VANSAH_URL = "https://prodau.vansah.com"  # Base URL for Vansah API
TEST_CASE = "TF-C4"  # Vansah test case key

# Create an instance of VansahNode
vansahnode = VansahNode()

# Set up VansahNode configuration
vansahnode.set_vansah_url(VANSAH_URL)  # Set the Vansah API URL
vansahnode.set_sprint_name("TF Sprint 1")  # Specify the sprint name
vansahnode.set_environment_name("UAT")  # Define the environment (e.g., UAT, PROD)
vansahnode.set_release_name("TestingTRUNK")  # Set the release name

# Set the API token for authentication (replace with your actual token)
vansahnode.set_vansah_token(
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.**********************************************pHuaoEf9yVhlk"
)

# Link the JIRA issue key to the test run
vansahnode.set_jira_issue_key(JIRA_ISSUE_KEY)

# Create a test run for the specified test case
vansahnode.add_test_run_from_jira_issue(TEST_CASE)

# Add test logs for specific test steps with results and comments
# Each test step is linked to a screenshot (optional)

# Adding log for step 1
vansahnode.add_test_log(
    result="passed",  # Result of the test step (e.g., passed, failed)
    comment="This is my log",  # A comment describing the test step result
    test_step_row=1,  # Step number in the test case
    image_path=r"C:\Users\***\Test Asset\******436908.png"  # Path to a screenshot (if applicable)
)

# Adding log for step 2
vansahnode.add_test_log(
    result="passed",
    comment="This is my log 2",
    test_step_row=2,
    image_path=r"C:\Users\***\Test Asset\******436908.png"
)

# Optional operations
# Uncomment these lines if you want to explore additional operations:

# Get the number of test steps in a test case
# vansahnode.test_step_count(TEST_CASE)

# Add a quick test from a test folder
# vansahnode.add_quick_test_from_test_folder(TEST_CASE, "passed")

# Remove a specific test log (requires TEST_LOG_IDENTIFIER to be set)
# vansahnode.remove_test_log()

# Remove the entire test run (requires TEST_RUN_IDENTIFIER to be set)
# vansahnode.remove_test_run()

# This script demonstrates basic usage of the VansahNode class to manage test cases,
# test logs, and interactions with the Vansah API. Modify the variables and configurations
# as needed for your specific use case.
