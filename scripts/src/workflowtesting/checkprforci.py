import re
import argparse
import sys
import requests
import json
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def check_if_ci_only_is_modified(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1

    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    pattern_workflow = re.compile(r".github/workflows/.*")
    pattern_script = re.compile(r"scripts/.*")
    pattern_test = re.compile(r"tests/.*")
    pattern_test_config = re.compile(r"tests/test-config.yaml")
    page_number = 1
    max_page_size,page_size = 100,100

    workflow_found = False
    other_found = False

    while (page_size == max_page_size) & (not other_found):

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        r = requests.get(files_api_query,headers=headers)
        files = r.json()
        page_size = len(files)
        page_number += 1


        for f in files:
            filename = f["filename"]
            if pattern_workflow.match(filename):
                workflow_found = True
            elif pattern_script.match(filename):
                workflow_found = True
            elif pattern_test_config.match(filename):
                workflow_found = True
                test_config_path = filename
            elif pattern_test.match(filename):
                workflow_found = True
            else:
                other_found = True
                break

    tests = "none"
    if not other_found:
        if test_config_path:
            test_config_data = open(test_config_path).read()
            test_config = json.loads(test_config_data)
            if "vendor-type" in test_config:
                vendor_type = test_config["vendor-type"]
                print(f"::set-output name=vendor_type::{vendor_type}")
            tests = "manual"
        else:
            tests = "auto"
    return tests



def verify_user(username):
    print(f"[INFO] Verify user. {username}")
    owners_path = os.path.join("charts", "OWNERS")
    if not os.path.exists(owners_path):
        print(f"[ERROR] {owners_path} file does not exist.")
    else:
        data = open(owners_path).read()
        out = yaml.load(data, Loader=Loader)
        if username in out['approvers']:
           return True
        else:
           print(f"[ERROR] {username} cannot run tests")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    parser.add_argument("-n", "--verify-user", dest="username", type=str, required=True,
                        help="check if the user can run tests")
    args = parser.parse_args()
    if verify_user(args.username):
        test_type = check_if_ci_only_is_modified(args.api_url)
        print(f"::set-output name=test_type::{test_type}")


if __name__ == "__main__":
    main()
