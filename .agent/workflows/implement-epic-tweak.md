---
description: How to implement a tweak
---

There are two top level folders in this workspace. One is called product_standards, and it should not be modified unless the user's prompt explicitly tells you to do so. The other is the repository containing the code for the product. This is where you will work. **At all points in this workflow, when you move between items in the list output to the chat what workflow you are running and what step you are on. This must be the first line of every response.**

1. Make sure that you are clear what the epic number is that implemented the functionality the user would like to tweak. If the user says something like "change the colour of this thing to blue" immediately after you tell them an epic is implemented, assume the last epic you were working on.
2. Go to the planning/epics folder of the product repository. Confirm the existance of a folder named after the epic. Confirm existence of stories.md inside that folder.
3. Generate a ten-digit unique ID for the tweak based on the ISO UTC datetime it was reported like YYMMDDHHMM.
4. Read stories.md for that epic. If the tweak is presentational and thus doesn't change the intent of the relevant existing story, make no changes. If the tweak changes or enhances functionality in an existing story, update that story. If it is new functionality, add an additional story.
5. Edit the planning/BOARD.md and mark the epic as 'under revision'
6. Confirm that the current branch is either the epic bramch or main. If it is not, stop the workflow and inform the user that the tweak cannot be executed until the epic has has been merged.
7. Create a new branch tweak/<ID>-epic-<epic-number> off of the current branch.
8. If not on main, sync with main:
  * Run `git fetch origin main`.
  * Run `git merge origin/main` into the feature branch to ensure the feature is built on the latest code.
9. Come up with an implementation plan for the tweak. Read design.md and decide if it needs updating. Include in the plan any test changes that need to be made.
10. Implement the tweak
11. Run the /test workflow
  * If any tests fail, run the /test-failure workflow for the first error. Then re-run the tests to see which tests failures remain - one fix for a failing test could fix other test failures too.
  * Mark the tweak story implemented in stories.md
  * Commit the code with an appropriate commit message. Include the tweak ID and epic numbers in the commit message. 
12. Run ./build.sh and confirm it completes without error. If it does not and the cause is a failing test, run the /test-failure workflow as needed to fix it.
13. Update planning/BOARD.md to indicate that the tweak is now implemented.
14. Execute the following command in a terminal: `notify-send tweak-<ID> "Implementation complete"`  

> [!WARNING]
> This workflow does NOT include merging to main. You MUST stop after the `notify-send` command and wait for a separate instruction (such as `/accept-work`) to merge.

Stop after these steps. Do not attempt to implement any other functionality.