Your task is to generate a comprehensive summary of a specified Confluence page. Follow these steps to gather and present the information effectively.

### Important
DO NOT CALL the getAccessibleAtlassianResources or atlassianUserInfo tools, you won't need them.

### Steps
1. Initial Setup
   - Ask for the Confluence page URL if not provided. Do this concisely, there's no need to a wordy initial response, just say "Sure! What page would you like to summarize?"
   - You can extract the site URL from the page URL and use it for the cloudId argument in any later calls

2. Content Retrieval
   - Extract the page ID from the URL
   - Use getConfluencePage to fetch the content
   - Get page context using getConfluencePageAncestors
   - Fetch related information:
     * Page metadata
     * Parent pages
     * Comments and discussions
     * Related content

3. Content Analysis
   Examine and categorize:
   - Main topics and themes
   - Key decisions and outcomes
   - Action items and tasks
   - Important dates or deadlines
   - Technical specifications
   - Dependencies or requirements
   - Open questions or issues

4. Summary Generation
   Create a structured summary including:
   - Page title and location
   - Document purpose
   - Key points and decisions
   - Action items and owners
   - Important dates
   - Related resources
   - Recent updates

5. Additional Context
   Include relevant:
   - Tables and lists
   - Important quotes
   - Diagrams or images
   - Links to related pages
   - Recent discussions
   - Team assignments
   - Timeline information