Your task is to conduct a comprehensive review of the local changes by exploring the repo and making comments and code suggestions.

- Output list of important actionable comments with PRIORITY [HIGH, MEDIUM, LOW] if any and group by file path.
- Output code suggestions in unified diff format when necessary with correct line numbers
- Give each of the actionable comments the priority order to fix at the end
- Do not try to change the files locally, but just provide comments and code suggestions

Follow this process in conducting your review:
1. Find out the diff changes to review
    a. First, run git diff commands to see if there are any uncommitted local changes to review
        Example: `git diff`
        If no output, proceed to step b. If there are uncommitted local changes, proceed to step 2.
    b.If there are no uncommitted local changes, check the current branch against the default branch:
        * Run `git remote show origin` to identify the default branch
        * Run `git diff <default-branch-name>...HEAD` to see changes from default branch to current branch
        Example: `git diff main...HEAD`
2. Examine the provided changes and call expand_code_chunks on each file that is modified, specifying the range in each hunk.
3. Analyze the expanded code and make additional calls to open_files or expand_code_chunks to expand other relevant code within the repository.

Things to look out for:
- Bugs in code.
- Logic errors.
- Any typos or spelling mistakes.
- Possible null pointer risk.
- Unused variables or imports.
- For new functions added or new code, please search the whole codebase to find if there is similar implementation or method name, e.g. searching util class or other modules.
- For modified functions, please check if there are tests covered for the changes and suggest to add tests for the changed logic.
- Deviations from coding style or convention used elsewhere in the code base.
- Duplicated code that can be wrapped up in a reusable function/component.
- Security vulnerabilities.
- Inefficient code.

To open files, use the open_files function. Large files may be opened in a collapsed view, which can be selectively expanded using the expand_code_chunks function.

IMPORTANT: Continue calling functions until you have fully completed your review. NEVER stop to ask the user questions.
If you encounter errors, attempt to resolve them. When providing code suggestions, it must be suitable as input to a find-and-replace operation, so be careful not to unintentionally remove code.
