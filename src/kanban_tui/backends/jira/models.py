from pydantic import BaseModel
# TODO
# Use a new model or reuse existing one?


class JiraIssue(BaseModel):
    assignee: str
    key: str


class JiraProject(BaseModel): ...


class JiraStatus(BaseModel): ...


class JiraUser(BaseModel): ...
