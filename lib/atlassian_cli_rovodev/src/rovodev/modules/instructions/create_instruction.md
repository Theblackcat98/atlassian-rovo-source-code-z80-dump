Your goal is to collect information for instruction definition and save it in the following format. You don't need to search the codebase to start, but follow the following steps:

Follow the following steps:
1. Ask the user about the name of the instruction
2. Ask about the description of the instruction
3. Ask about the content of the instruction
5. Save the instruction metadata into .rovodev/instructions.yml and the content into a markdown file in the .rovodev/ folder. Make sure to save the file in the correct format and do not overwrite existing instructions.

Follow the following yaml structure for .rovodev/instructions.yml:

```yaml
instructions:
- name: <name of the task>
    description: <description of the task>
    content_file: <path to the markdown file __relative to this file__ - i.e., without the .rovodev prefix>
````
