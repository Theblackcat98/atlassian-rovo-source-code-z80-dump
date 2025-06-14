## Summarize Jira Issues

### Prerequisites
If not already available in the conversation history, ask the user for their Atlassian site URL. DO THIS BEFORE ANYTHING ELSE.

DO NOT CALL the getAccessibleAtlassianResources or atlassianUserInfo tools, you won't need them.

### Steps
- Use the `searchJiraIssuesUsingJql` tool to fetch the issues
  - You should provide the site URL as the cloudId and in the jql argument, ensure you use "assignee = currentUser()"
- For each issue, collect:
   - Issue key and summary
   - Status
   - Priority (if set)
   - Due date (if set)
   - Recent updates

### Output Format
Organize the summary in sections:
1. High-priority or overdue issues
2. Issues in progress
3. Issues pending review/approval
4. Backlog items

For each issue, provide:
- A brief description of what the issue is about
- Current status and any blockers
- Recent activity or updates
- Links to the full issue for more details