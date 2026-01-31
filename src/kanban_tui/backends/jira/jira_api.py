from atlassian.jira import Jira
import asyncio
from functools import partial


def authenticate_to_jira(base_url: str, api_token: str, cert_path: str) -> Jira:
    auth = Jira(url=base_url, token=api_token, verify_ssl=cert_path)
    return auth


def get_jql(auth: Jira, jql: str):
    """Execute JQL query - blocking call"""
    return auth.jql(jql)


async def get_jql_async(auth: Jira, jql: str):
    """Execute JQL query asynchronously in thread pool to avoid blocking UI"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(get_jql, auth, jql))


def get_all_issues(auth: Jira, project: str):
    return auth.get_all_project_issues(project)


def get_transitions(auth: Jira, issue_key: str):
    """Get available transitions for a specific issue"""
    return auth.get_issue_transitions(issue_key)


async def get_transitions_async(auth: Jira, issue_key: str):
    """Get available transitions asynchronously in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(get_transitions, auth, issue_key))
