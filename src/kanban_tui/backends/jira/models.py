from pydantic import BaseModel


class JiraIssue(BaseModel):
    assignee: str
    key: str
    ...


class JiraProject(BaseModel): ...


class JiraStatus(BaseModel): ...


class JiraUser(BaseModel): ...
