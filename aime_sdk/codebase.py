"""
AIME Toolset SDK: `codebase`

The server provides various apis to access the Codebase repository, including:
- Repository: Get/list repositories, branches, and commits; create branches
- Merge Requests (MR): Get/list/create/merge/update/comment on MRs; view MR diffs and comments; check mergeability. Supports both Codebase MRs (https://code.byted.org/ or https://bits.bytedance.net/code/) and Bits MRs (https://bits.bytedance.net/devops/).
- User: Retrieve current authenticated user info.
Note: Not suitable for exploring/editing files in the repository, use git instead.
Terminology:
- **Codebase** refers to company's private git hosting platform (like github, gitlab, etc). The original "codebase" term is usually called repository in the company. Platform URL: https://code.byted.org/ and https://bits.bytedance.net/code/.
MR stands for Merge Request, it's a feature provided by company's git hosting platform.
- **MR(Merge request)** is a request to merge changes from one non-default branch into another specified branch, which is commonly the master or main branch.
	- Codebase MR URL format: https://code.byted.org/{repo_name}/merge_requests/{mr_id} or https://bits.bytedance.net/code/{repo_name}/merge_requests/{mr_id}
  - Bits MR URL format: https://bits.bytedance.net/devops/{project_id}/code/detail/{cr_id}

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.codebase import mcp_codebase_CountUserActivities
    result = mcp_codebase_CountUserActivities(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'codebase'


def mcp_codebase_CountUserActivities(
    *,
    EndDate: Optional[str] = None,
    StartDate: Optional[str] = None,
    TenantId: Optional[str] = None,
    Username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Count user activities by date range.
    It returns the count of user activities within the specified date range.

    AIME tool: `mcp:codebase_CountUserActivities`

    Args:
        EndDate (str, optional): Optional. End date (YYYY-MM-DD format). If StartDate and EndDate are not both provided, use now.
        StartDate (str, optional): Optional. Start date (YYYY-MM-DD format). If StartDate and EndDate are not both provided, use now-365days.
        TenantId (str, optional): Optional. Tenant ID. If Username and TenantId are not provided, use self.
        Username (str, optional): Optional. Username. If Username and TenantId are not provided, use self.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if EndDate is not None:
        _params['EndDate'] = EndDate
    if StartDate is not None:
        _params['StartDate'] = StartDate
    if TenantId is not None:
        _params['TenantId'] = TenantId
    if Username is not None:
        _params['Username'] = Username
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_CountUserActivities',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_CreateIssue(
    *,
    RepoId: str,
    Title: str,
    AssigneeIds: Optional[List[str]] = None,
    Description: Optional[str] = None,
    DueDate: Optional[str] = None,
    LabelIds: Optional[List[str]] = None,
    ParentIssueId: Optional[str] = None,
    Status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an issue in a repository.

    AIME tool: `mcp:codebase_CreateIssue`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Title (str, required): Title of the issue.
        AssigneeIds (List[str], optional): Optional. List of user IDs to assign to the issue.
        Description (str, optional): Optional. Description of the issue.
        DueDate (str, optional): Optional. Due date for the issue. e.g. `2006-01-02`.
        LabelIds (List[str], optional): Optional. List of label IDs to apply to the issue.
        ParentIssueId (str, optional): Optional. Parent issue ID to create this as a sub-issue.
        Status (str, optional): Optional. Initial status for the issue. Default: "backlog". One of: todo, done, canceled, in_progress, backlog.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Title'] = Title
    if AssigneeIds is not None:
        _params['AssigneeIds'] = AssigneeIds
    if Description is not None:
        _params['Description'] = Description
    if DueDate is not None:
        _params['DueDate'] = DueDate
    if LabelIds is not None:
        _params['LabelIds'] = LabelIds
    if ParentIssueId is not None:
        _params['ParentIssueId'] = ParentIssueId
    if Status is not None:
        _params['Status'] = Status
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_CreateIssue',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetCommit(
    *,
    RepoId: str,
    Revision: str,
) -> Dict[str, Any]:
    """
    Get a specific commit.

    AIME tool: `mcp:codebase_GetCommit`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Revision (str, required): The commit ID or other git reference (branch, tag).

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Revision'] = Revision
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetCommit',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetIssue(
    *,
    RepoId: str,
    Number: int,
) -> Dict[str, Any]:
    """
    Get an issue.

    AIME tool: `mcp:codebase_GetIssue`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the issue.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetIssue',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetMe(
    *,
    Reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get my self (an authenticated Codebase user or an application).
    It returns the information of myself. Consider to use this when a request include "me", "my", "我".

    AIME tool: `mcp:codebase_GetMe`

    Args:
        Reason (str, optional): Optional. Reason the session was created.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if Reason is not None:
        _params['Reason'] = Reason
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetMe',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetMergeRequest(
    *,
    RepoId: str,
    Number: int,
) -> Dict[str, Any]:
    """
    Get a merge request (abbreviated as MR).

    AIME tool: `mcp:codebase_GetMergeRequest`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetMergeRequest',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetMergeRequestMergeability(
    *,
    RepoId: str,
    Number: int,
) -> Dict[str, Any]:
    """
    Get the mergeability of a merge request.

    AIME tool: `mcp:codebase_GetMergeRequestMergeability`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetMergeRequestMergeability',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetMergeRequestReviewStatus(
    *,
    RepoId: str,
    Number: int,
) -> Dict[str, Any]:
    """
    Get the review status of a merge request.

    AIME tool: `mcp:codebase_GetMergeRequestReviewStatus`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetMergeRequestReviewStatus',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetRepository(
    *,
    Id: Optional[str] = None,
    Path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get a repository either by ID (e.g. 123456) or path (e.g. path/to/repo). Either of the `Id` or `Path` must be provided.

    AIME tool: `mcp:codebase_GetRepository`

    Args:
        Id (str, optional): Optional. The ID of the repository.
        Path (str, optional): Optional. The full path of the repository like "path/to/repo". You can get the repo ID by known repo path.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if Id is not None:
        _params['Id'] = Id
    if Path is not None:
        _params['Path'] = Path
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetRepository',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_GetUserStatistics(
    *,
    NaturalYear: Optional[int] = None,
    RelativeDays: Optional[int] = None,
    UserId: Optional[str] = None,
    Username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get user statistics for a specific user.
    It returns the statistics information of the specified user.

    AIME tool: `mcp:codebase_GetUserStatistics`

    Args:
        NaturalYear (int, optional): Optional. Natural year to fetch statistics for. Data available only from 2022 onwards.
        RelativeDays (int, optional): Optional. Relative time range in days to fetch statistics for. Enum values: 7 / 30 / 180 / 365. Defaults to 365 if both RelativeDays and NaturalYear are not provided.
        UserId (str, optional): Optional. ID of the user to fetch statistics for. Returns self if both Id and Username are empty.
        Username (str, optional): Optional. Username of the user to fetch statistics for. Returns self if both Id and Username are empty.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if NaturalYear is not None:
        _params['NaturalYear'] = NaturalYear
    if RelativeDays is not None:
        _params['RelativeDays'] = RelativeDays
    if UserId is not None:
        _params['UserId'] = UserId
    if Username is not None:
        _params['Username'] = Username
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_GetUserStatistics',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListBranches(
    *,
    RepoId: str,
    PageNumber: Optional[int] = None,
    PageSize: Optional[int] = None,
    Query: Optional[str] = None,
    QueryMode: Optional[str] = None,
    Type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List branches.

    AIME tool: `mcp:codebase_ListBranches`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        PageNumber (int, optional): Pagination number, starts from 1.
        PageSize (int, optional): Pagination size. Maximum 100, default is 10.
        Query (str, optional): Search query, such as `feat` to match `add_new_feat` or `feat/new_page`. Valid only when Type is `all`.
        QueryMode (str, optional): Query mode. Default: `substr`. One of: substr, prefix, suffix, glob, wildcard.
        Type (str, optional): Branch type. Default: `all`. One of: all, merged, active, stale, yours.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    if PageNumber is not None:
        _params['PageNumber'] = PageNumber
    if PageSize is not None:
        _params['PageSize'] = PageSize
    if Query is not None:
        _params['Query'] = Query
    if QueryMode is not None:
        _params['QueryMode'] = QueryMode
    if Type is not None:
        _params['Type'] = Type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListBranches',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListCommitDiffFiles(
    *,
    RepoId: str,
    FromCommit: str,
    ToCommit: str,
    Context: Optional[int] = None,
    Excludes: Optional[List[str]] = None,
    FilesOnly: Optional[bool] = None,
    Includes: Optional[List[str]] = None,
    IsStraight: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    List the diff files (diff metadata or diff patch) between two commits (or a single commit). Large diff files will be pruned.

    AIME tool: `mcp:codebase_ListCommitDiffFiles`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        FromCommit (str, required): The commit ID to list diff files from. If empty, it will returns the diff for the commit `ToCommit` only.
        ToCommit (str, required): The commit ID to list diff files to.
        Context (int, optional): How many lines of diff context should be returned. Default is 3.
        Excludes (List[str], optional): Excludes diff files that match the patterns (supports wlidcard). If empty, no diff files will be excluded.
        FilesOnly (bool, optional): Whether to return only the diff file metadata. Default is false.
        Includes (List[str], optional): Includes diff files that match the patterns (supports wlidcard). If empty, all diff files will be included.
        IsStraight (bool, optional): Whether to use two-dot diff (straight diff). Default is true (two-dot diff). Set to false for three-dot diff.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['FromCommit'] = FromCommit
    _params['ToCommit'] = ToCommit
    if Context is not None:
        _params['Context'] = Context
    if Excludes is not None:
        _params['Excludes'] = Excludes
    if FilesOnly is not None:
        _params['FilesOnly'] = FilesOnly
    if Includes is not None:
        _params['Includes'] = Includes
    if IsStraight is not None:
        _params['IsStraight'] = IsStraight
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListCommitDiffFiles',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListCommits(
    *,
    RepoId: str,
    Revision: str,
    Author: Optional[str] = None,
    PageNumber: Optional[int] = None,
    PageSize: Optional[int] = None,
    Path: Optional[str] = None,
    Query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List commits.

    AIME tool: `mcp:codebase_ListCommits`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Revision (str, required): The revision to list commits from.
        Author (str, optional): Show commits authored by a specific author's username.
        PageNumber (int, optional): Pagination number, starts from 1.
        PageSize (int, optional): Pagination size. Default is 10.
        Path (str, optional): List commit history for the given path, empty for the whole repository.
        Query (str, optional): Show commits with message (includes title and body) that matches the specified pattern.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Revision'] = Revision
    if Author is not None:
        _params['Author'] = Author
    if PageNumber is not None:
        _params['PageNumber'] = PageNumber
    if PageSize is not None:
        _params['PageSize'] = PageSize
    if Path is not None:
        _params['Path'] = Path
    if Query is not None:
        _params['Query'] = Query
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListCommits',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListMergeRequestCheckRuns(
    *,
    RepoId: str,
    Number: int,
    Unsuccessful: bool,
    PageNumber: int,
    PageSize: int,
    Query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List check runs for a merge request.

    AIME tool: `mcp:codebase_ListMergeRequestCheckRuns`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.
        Unsuccessful (bool, required): `true` means filter unsuccessful check runs (pending, running, failed, warning, etc.). Default is `false`.
        PageNumber (int, required): Pagination number, starts from 1.
        PageSize (int, required): Pagination size. Maximum 100, default is 10.
        Query (str, optional): Optional. Search text to match against check run name and description (case-insensitive, substring match).

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    _params['Unsuccessful'] = Unsuccessful
    _params['PageNumber'] = PageNumber
    _params['PageSize'] = PageSize
    if Query is not None:
        _params['Query'] = Query
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListMergeRequestCheckRuns',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListMergeRequestComments(
    *,
    RepoId: str,
    Number: int,
    Outdated: Optional[bool] = None,
    PageNumber: Optional[int] = None,
    PageSize: Optional[int] = None,
    Query: Optional[str] = None,
    Status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List comments in a merge request.

    AIME tool: `mcp:codebase_ListMergeRequestComments`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.
        Outdated (bool, optional): Optional. Filter by outdated comments. Set to false to exclude outdated comments; set to true to include only outdated comments. If not set, returns all comments regardless of outdated status.
        PageNumber (int, optional): Optional. Pagination number, starts from 1.
        PageSize (int, optional): Optional. Pagination size. Default is no limit.
        Query (str, optional): Optional. Filter by comment content.
        Status (str, optional): Optional. Filter by comment status. If not set, returns both open and resolved comments. One of: open, resolved.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    if Outdated is not None:
        _params['Outdated'] = Outdated
    if PageNumber is not None:
        _params['PageNumber'] = PageNumber
    if PageSize is not None:
        _params['PageSize'] = PageSize
    if Query is not None:
        _params['Query'] = Query
    if Status is not None:
        _params['Status'] = Status
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListMergeRequestComments',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListMergeRequestDiffFiles(
    *,
    RepoId: str,
    Number: int,
    Context: Optional[int] = None,
    Excludes: Optional[List[str]] = None,
    FilesOnly: Optional[bool] = None,
    Includes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    List the diff files (diff metadata or diff patch) of a merge request on the latest version. Large diff files will be pruned.

    AIME tool: `mcp:codebase_ListMergeRequestDiffFiles`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.
        Context (int, optional): How many lines of diff context should be returned. Default is 3.
        Excludes (List[str], optional): Excludes diff files that match the patterns (supports wlidcard). If empty, no diff files will be excluded.
        FilesOnly (bool, optional): Whether to return only the diff file metadata. Default is false.
        Includes (List[str], optional): Includes diff files that match the patterns (supports wlidcard). If empty, all diff files will be included.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    if Context is not None:
        _params['Context'] = Context
    if Excludes is not None:
        _params['Excludes'] = Excludes
    if FilesOnly is not None:
        _params['FilesOnly'] = FilesOnly
    if Includes is not None:
        _params['Includes'] = Includes
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListMergeRequestDiffFiles',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListMergeRequests(
    *,
    RepoId: str,
    Author: Optional[str] = None,
    CommitId: Optional[str] = None,
    Draft: Optional[bool] = None,
    Labels: Optional[List[str]] = None,
    PageNumber: Optional[int] = None,
    PageSize: Optional[int] = None,
    ReviewStatus: Optional[str] = None,
    Reviewer: Optional[str] = None,
    SortBy: Optional[str] = None,
    SortOrder: Optional[str] = None,
    SourceBranch: Optional[str] = None,
    Status: Optional[str] = None,
    TargetBranch: Optional[str] = None,
    Title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List merge requests in a repository.

    AIME tool: `mcp:codebase_ListMergeRequests`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Author (str, optional): Optional. Filter by the author's username.
        CommitId (str, optional): Optional. The commit ID must be complete.
        Draft (bool, optional): Optional. Draft means not ready to be reviewed or merged.
        Labels (List[str], optional)
        PageNumber (int, optional): Optional. Pagination number, starts from 1.
        PageSize (int, optional): Optional. Pagination size. Default is 10.
        ReviewStatus (str, optional): Optional. Filter by review status. One of: pending, passed, disapproved.
        Reviewer (str, optional): Optional. Filter by the reviewer's username.
        SortBy (str, optional): Optional. One of: CreatedAt, UpdatedAt.
        SortOrder (str, optional): Optional. One of: Asc, Desc.
        SourceBranch (str, optional): Optional. Filter by the source branch name.
        Status (str, optional): Optional. Filter by merge request status. One of: open, closed, merged.
        TargetBranch (str, optional): Optional. Filter by the target branch name.
        Title (str, optional): Optional.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    if Author is not None:
        _params['Author'] = Author
    if CommitId is not None:
        _params['CommitId'] = CommitId
    if Draft is not None:
        _params['Draft'] = Draft
    if Labels is not None:
        _params['Labels'] = Labels
    if PageNumber is not None:
        _params['PageNumber'] = PageNumber
    if PageSize is not None:
        _params['PageSize'] = PageSize
    if ReviewStatus is not None:
        _params['ReviewStatus'] = ReviewStatus
    if Reviewer is not None:
        _params['Reviewer'] = Reviewer
    if SortBy is not None:
        _params['SortBy'] = SortBy
    if SortOrder is not None:
        _params['SortOrder'] = SortOrder
    if SourceBranch is not None:
        _params['SourceBranch'] = SourceBranch
    if Status is not None:
        _params['Status'] = Status
    if TargetBranch is not None:
        _params['TargetBranch'] = TargetBranch
    if Title is not None:
        _params['Title'] = Title
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListMergeRequests',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListRepositories(
    *,
    ContributedById: Optional[str] = None,
    PageNumber: Optional[int] = None,
    PageSize: Optional[int] = None,
    Query: Optional[str] = None,
    SortBy: Optional[str] = None,
    SortOrder: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List repositories with various filters.
    If you want to get a repository by known repo ID or path (e.g. path/to/repo), it's better to use `GetRepository`.

    AIME tool: `mcp:codebase_ListRepositories`

    Args:
        ContributedById (str, optional): Optional. Filter repositories by contributor ID. Requires that the specified user has contributed to the repository. If `ContributedById` is specified, no other filters are allowed.
        PageNumber (int, optional): Optional. Pagination number, starts from 1.
        PageSize (int, optional): Optional. Pagination size. Maximum 100, default is 10.
        Query (str, optional): Optional. Filter repositories by path. Matches either the full repository path prefix or the prefix of the last segment in the path.
        SortBy (str, optional): Optional. Sort results by either the last activity time (`PushedAt`), repository path (`Path`) or the time of my last contribution (`ContributedAt`). Default is `ContributedAt`. One of: PushedAt, Path, ContributedAt.
        SortOrder (str, optional): Optional. Sort order: `Asc` or `Desc`. One of: Asc, Desc.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if ContributedById is not None:
        _params['ContributedById'] = ContributedById
    if PageNumber is not None:
        _params['PageNumber'] = PageNumber
    if PageSize is not None:
        _params['PageSize'] = PageSize
    if Query is not None:
        _params['Query'] = Query
    if SortBy is not None:
        _params['SortBy'] = SortBy
    if SortOrder is not None:
        _params['SortOrder'] = SortOrder
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListRepositories',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListReviewNetworkStatistics(
    *,
    AuthorId: Optional[str] = None,
    AuthorUsername: Optional[str] = None,
    ReviewerId: Optional[str] = None,
    ReviewerUsername: Optional[str] = None,
    TopN: Optional[int] = None,
) -> Dict[str, Any]:
    """
    List review network statistics.
    It returns the review network statistics based on the specified criteria.
    Use self as author if both author and reviewer are empty.

    AIME tool: `mcp:codebase_ListReviewNetworkStatistics`

    Args:
        AuthorId (str, optional): Optional. ID of the author to filter by.
        AuthorUsername (str, optional): Optional. Username of the author to filter by.
        ReviewerId (str, optional): Optional. ID of the reviewer to filter by.
        ReviewerUsername (str, optional): Optional. Username of the reviewer to filter by.
        TopN (int, optional): Optional. Number of top results to return. Default 3.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if AuthorId is not None:
        _params['AuthorId'] = AuthorId
    if AuthorUsername is not None:
        _params['AuthorUsername'] = AuthorUsername
    if ReviewerId is not None:
        _params['ReviewerId'] = ReviewerId
    if ReviewerUsername is not None:
        _params['ReviewerUsername'] = ReviewerUsername
    if TopN is not None:
        _params['TopN'] = TopN
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListReviewNetworkStatistics',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_ListWorkItemLinks(
    *,
    RepoId: str,
    Number: int,
    PageNumber: Optional[int] = None,
    PageSize: Optional[int] = None,
) -> Dict[str, Any]:
    """
    List work item links(such as meego, ttjira, issue) for a merge request.

    AIME tool: `mcp:codebase_ListWorkItemLinks`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.
        PageNumber (int, optional): Optional. Pagination number, starts from 1.
        PageSize (int, optional): Optional. Pagination size. Maximum 100, default is 10.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    if PageNumber is not None:
        _params['PageNumber'] = PageNumber
    if PageSize is not None:
        _params['PageSize'] = PageSize
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_ListWorkItemLinks',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_MergeMergeRequest(
    *,
    RepoId: str,
    Number: int,
) -> Dict[str, Any]:
    """
    Merge a merge request.

    AIME tool: `mcp:codebase_MergeMergeRequest`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_MergeMergeRequest',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_PublishDraftComments(
    *,
    RepoId: str,
    Number: int,
    ReviewContent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Publish all draft comments previously created in this merge request.

    AIME tool: `mcp:codebase_PublishDraftComments`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.
        ReviewContent (str, optional): Optional. The summary review content to include for publishing.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    if ReviewContent is not None:
        _params['ReviewContent'] = ReviewContent
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_PublishDraftComments',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_SearchIssues(
    *,
    Assignee: Optional[str] = None,
    DueDateSince: Optional[str] = None,
    DueDateUntil: Optional[str] = None,
    PageSize: Optional[int] = None,
    PageToken: Optional[str] = None,
    Query: Optional[str] = None,
    RepoId: Optional[str] = None,
    SortBy: Optional[str] = None,
    SortOrder: Optional[str] = None,
    Status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search issues across repositories or within a specific repository.

    AIME tool: `mcp:codebase_SearchIssues`

    Args:
        Assignee (str, optional): Optional. Filter by assignee username. Only returns issues assigned to the specified user.
        DueDateSince (str, optional): Optional. Filter issues with due dates on or after this date. Use RFC3339 format (e.g. "2024-01-15T00:00:00Z").
        DueDateUntil (str, optional): Optional. Filter issues with due dates on or before this date. Use RFC3339 format (e.g. "2024-12-31T23:59:59Z").
        PageSize (int, optional): Optional. Number of issues to return per page. Must be between 1-100. Default: 10.
        PageToken (str, optional): Optional. Pagination token from previous response. Leave empty to get the first page.
        Query (str, optional): Optional. Search text to match against issue titles and descriptions. Supports partial matching.
        RepoId (str, optional): Optional. Repository to search in. Can be repository ID (e.g. "123456") or full path (e.g. "company/project"). If not specified, searches across all accessible repositories.
        SortBy (str, optional): Optional. Sort field: "CreatedAt" (when issue was created) or "UpdatedAt" (when issue was last modified). Default: "UpdatedAt". One of: CreatedAt, UpdatedAt.
        SortOrder (str, optional): Optional. Sort direction: "Asc" (oldest first) or "Desc" (newest first). Default: "Desc". One of: Asc, Desc.
        Status (str, optional): Optional. Filter by issue status. Available options: "backlog" (not started), "todo" (ready to work), "in_progress" (being worked on), "done" (completed), "canceled" (abandoned). One of: todo, done, canceled, in_progress, backlog.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if Assignee is not None:
        _params['Assignee'] = Assignee
    if DueDateSince is not None:
        _params['DueDateSince'] = DueDateSince
    if DueDateUntil is not None:
        _params['DueDateUntil'] = DueDateUntil
    if PageSize is not None:
        _params['PageSize'] = PageSize
    if PageToken is not None:
        _params['PageToken'] = PageToken
    if Query is not None:
        _params['Query'] = Query
    if RepoId is not None:
        _params['RepoId'] = RepoId
    if SortBy is not None:
        _params['SortBy'] = SortBy
    if SortOrder is not None:
        _params['SortOrder'] = SortOrder
    if Status is not None:
        _params['Status'] = Status
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_SearchIssues',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_UpdateIssue(
    *,
    RepoId: str,
    Number: int,
    AssigneeIds: Optional[List[str]] = None,
    Description: Optional[str] = None,
    DueDate: Optional[str] = None,
    ParentIssueId: Optional[str] = None,
    Status: Optional[str] = None,
    Title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing issue.

    AIME tool: `mcp:codebase_UpdateIssue`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the issue.
        AssigneeIds (List[str], optional): Optional. New list of user IDs to assign to the issue. If not provided, assignees remain unchanged. If empty array is provided, all assignees will be removed.
        Description (str, optional): Optional. New description for the issue.
        DueDate (str, optional): Optional. New due date for the issue. e.g. "2006-01-02". Set to empty string to clear due date.
        ParentIssueId (str, optional): Optional. New parent issue ID to change the parent-child relationship.
        Status (str, optional): Optional. New status for the issue. Available options: "backlog" (not started), "todo" (ready to work), "in_progress" (being worked on), "done" (completed), "canceled" (abandoned). One of: todo, done, canceled, in_progress, backlog.
        Title (str, optional): Optional. New title for the issue.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    if AssigneeIds is not None:
        _params['AssigneeIds'] = AssigneeIds
    if Description is not None:
        _params['Description'] = Description
    if DueDate is not None:
        _params['DueDate'] = DueDate
    if ParentIssueId is not None:
        _params['ParentIssueId'] = ParentIssueId
    if Status is not None:
        _params['Status'] = Status
    if Title is not None:
        _params['Title'] = Title
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_UpdateIssue',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_codebase_UpdateMergeRequest(
    *,
    RepoId: str,
    Number: int,
    AutoMerge: Optional[bool] = None,
    Description: Optional[str] = None,
    Draft: Optional[bool] = None,
    Title: Optional[str] = None,
    WorkItemIds: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Update a merge request.

    AIME tool: `mcp:codebase_UpdateMergeRequest`

    Args:
        RepoId (str, required): The ID or path (e.g. path/to/repo) of the repository.
        Number (int, required): The number of the merge request.
        AutoMerge (bool, optional): Whether to enable auto merge.
        Description (str, optional): The new description of the merge request.
        Draft (bool, optional): Whether the merge request is a draft. Draft means not ready to be reviewed or merged.
        Title (str, optional): The new title of the merge request.
        WorkItemIds (List[str], optional): The IDs of the work items (like Meego tickets) to link to the merge request.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['RepoId'] = RepoId
    _params['Number'] = Number
    if AutoMerge is not None:
        _params['AutoMerge'] = AutoMerge
    if Description is not None:
        _params['Description'] = Description
    if Draft is not None:
        _params['Draft'] = Draft
    if Title is not None:
        _params['Title'] = Title
    if WorkItemIds is not None:
        _params['WorkItemIds'] = WorkItemIds
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:codebase_UpdateMergeRequest',
        parameters=_params,
        response_format="raw",
    ).data


def submit_merge_request(
    *,
    repo_name: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str,
    draft: bool,
) -> Dict[str, Any]:
    """
    Submit a merge request to codebase

    AIME tool: `submit_merge_request`

    Args:
        repo_name (str, required): name of the repository to submit merge request
        source_branch (str, required): source branch to submit merge request
        target_branch (str, required): target branch to submit merge request
        title (str, required): title of the merge request
        description (str, required): description of the merge request
        draft (bool, required): whether to create a draft merge request, defaults to true

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['repo_name'] = repo_name
    _params['source_branch'] = source_branch
    _params['target_branch'] = target_branch
    _params['title'] = title
    _params['description'] = description
    _params['draft'] = draft
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='submit_merge_request',
        parameters=_params,
        response_format="raw",
    ).data


def create_merge_request_comment(
    *,
    repo_name: str,
    number: int,
    comments: List[Dict[str, Any]],
    locale: str,
    draft: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    create comments in a codebase MR, result will contain message, all comments, published count and ignore counts. You should use user preferred locale to generate the comments.

    AIME tool: `create_merge_request_comment`

    Args:
        repo_name (str, required): required, codebase repo name, eg group/repo
        number (int, required): required, the number of the merge request
        comments (List[Dict[str, Any]], required): required, comments list to create
        locale (str, required): required, locale for all comments (zh-CN or en-US). Use user preferred locale to generate the comment.
        draft (bool, optional): optional, whether to create the comment as a draft (invisible to others), default is false

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['repo_name'] = repo_name
    _params['number'] = number
    _params['comments'] = comments
    _params['locale'] = locale
    if draft is not None:
        _params['draft'] = draft
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='create_merge_request_comment',
        parameters=_params,
        response_format="raw",
    ).data


def add_merge_request_discussion(
    *,
    repo_name: str,
    number: int,
    comment: Dict[str, Any],
) -> Dict[str, Any]:
    """
    ONLY use this tool when the user explicitly requests posting a global comment on a merge request. This tool must NOT be used as a fallback when posting inline code comments fails. When attempting to add a similar global comment, prioritize updating an existing comment by providing its comment ID instead of creating a new one.

    AIME tool: `add_merge_request_discussion`

    Args:
        repo_name (str, required): codebase repo name, eg group/repo
        number (int, required): the number of the merge request
        comment (Dict[str, Any], required): global comment to create

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['repo_name'] = repo_name
    _params['number'] = number
    _params['comment'] = comment
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='add_merge_request_discussion',
        parameters=_params,
        response_format="raw",
    ).data


def get_merge_request_work_item_list(
    *,
    repo_id: str,
    merge_request_id: int,
) -> Dict[str, Any]:
    """
    get a merge request work item (meego) list

    AIME tool: `get_merge_request_work_item_list`

    Args:
        repo_id (str, required): codebase repo id
        merge_request_id (int, required): merge request Id，this Id is the **GetMergeRequest output Id instead of the Number

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['repo_id'] = repo_id
    _params['merge_request_id'] = merge_request_id
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='get_merge_request_work_item_list',
        parameters=_params,
        response_format="raw",
    ).data


def search_merge_requests(
    *,
    username: str,
    repo_paths: Optional[List[str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> Dict[str, Any]:
    """
    search merged merge requests by username and time range across all(default) or specified repositories, returns a json file path containing results grouped by repository, MRs within the file are sorted by time in descending order. At least one of 'username' or 'repo_paths' must be provided.

    AIME tool: `search_merge_requests`

    Args:
        username (str, required): Codebase username to filter merge requests by author. Must be a valid user ID (e.g., 'zhangsan.001'). Do not use Chinese display names or mixed formats.
        repo_paths (List[str], optional): Optional repository paths to filter merge requests (e.g., ['ugc/tiktok', 'ugc/douyin']). If not specified, searches all repositories.
        since (str, optional): Filter merge requests updated after this time. In RFC3339 format (e.g. '2006-01-02T15:04:05Z07:00').
        until (str, optional): Filter merge requests updated before this time. In RFC3339 format (e.g. '2006-01-02T15:04:05Z07:00').

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['username'] = username
    if repo_paths is not None:
        _params['repo_paths'] = repo_paths
    if since is not None:
        _params['since'] = since
    if until is not None:
        _params['until'] = until
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='search_merge_requests',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_bits_workflow_bits_workflow_get_mr_info(
    *,
    crUrl: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve MR detailed information by a Bits MR URL (only use this tool when the URL strictly follows the format: https://bits.bytedance.net/devops/{project_id}/code/detail/{cr_id}), including associated code repositories, branches, commits, and other data.

    AIME tool: `mcp:bits_workflow_bits_workflow_get_mr_info`

    Args:
        crUrl (str, optional): CR 的 URL

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if crUrl is not None:
        _params['crUrl'] = crUrl
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:bits_workflow_bits_workflow_get_mr_info',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'mcp_codebase_CountUserActivities',
    'mcp_codebase_CreateIssue',
    'mcp_codebase_GetCommit',
    'mcp_codebase_GetIssue',
    'mcp_codebase_GetMe',
    'mcp_codebase_GetMergeRequest',
    'mcp_codebase_GetMergeRequestMergeability',
    'mcp_codebase_GetMergeRequestReviewStatus',
    'mcp_codebase_GetRepository',
    'mcp_codebase_GetUserStatistics',
    'mcp_codebase_ListBranches',
    'mcp_codebase_ListCommitDiffFiles',
    'mcp_codebase_ListCommits',
    'mcp_codebase_ListMergeRequestCheckRuns',
    'mcp_codebase_ListMergeRequestComments',
    'mcp_codebase_ListMergeRequestDiffFiles',
    'mcp_codebase_ListMergeRequests',
    'mcp_codebase_ListRepositories',
    'mcp_codebase_ListReviewNetworkStatistics',
    'mcp_codebase_ListWorkItemLinks',
    'mcp_codebase_MergeMergeRequest',
    'mcp_codebase_PublishDraftComments',
    'mcp_codebase_SearchIssues',
    'mcp_codebase_UpdateIssue',
    'mcp_codebase_UpdateMergeRequest',
    'submit_merge_request',
    'create_merge_request_comment',
    'add_merge_request_discussion',
    'get_merge_request_work_item_list',
    'search_merge_requests',
    'mcp_bits_workflow_bits_workflow_get_mr_info',
]
