from atlassian.jira import Jira


def authenticate_to_jira(base_url: str, api_token: str, cert_path: str) -> Jira:
    auth = Jira(url=base_url, token=api_token, verify_ssl=cert_path)
    return auth


def get_jql(auth: Jira, jql: str):
    return auth.jql(jql)


def get_all_issues(auth: Jira, project: str):
    return auth.get_all_project_issues(project)


def get_transitions(auth: Jira, issue_key: str):
    """Get available transitions for a specific issue"""
    return auth.get_issue_transitions(issue_key)
