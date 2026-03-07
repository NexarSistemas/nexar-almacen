
# AI Integration – Final Step

To integrate AI prompts safely without affecting builds:

1. Place folders in the repository root:

   prompts/
   docs/ai/

2. Add the following lines to `.gitignore`:

   prompts/
   docs/ai/

3. Commit the `.gitignore` change.

4. If you want prompts synced across machines but not releases,
   you can instead use:

   prompts/
   docs/ai/
   !docs/ai/README.md

5. These files:
   - are ignored by packaging
   - will not affect builds
   - will not be included in installers

Recommended workflow:

Use the prompts when asking AI tools for help with the project.
Copy the content of the relevant prompt before interacting with the AI.
