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
    """Get available transitions asynchronously in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(get_jql, auth, jql))


def get_transitions(auth: Jira, issue_key: str):
    """Get available transitions for a specific issue"""
    return auth.get_issue_transitions(issue_key)


async def get_transitions_async(auth: Jira, issue_key: str):
    """Get available transitions asynchronously in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(get_transitions, auth, issue_key))


def set_issue_status(auth: Jira, issue_key: str, transition_id: int) -> dict:
    """Execute a transition to change issue status.

    Uses set_issue_status_by_transition_id which accepts a numeric
    transition ID, as opposed to auth.set_issue_status which expects
    a status *name* string.
    """
    try:
        auth.set_issue_status_by_transition_id(issue_key, transition_id)
        return {"success": True, "message": f"Transitioned {issue_key}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
