---
description: How to implement an epic
---

There are two top level folders in this workspace. One is called product_standards, and it should not be modified unless the user's prompt explicitly tells you to do so. The other is the repository containing the code for the product. This is where you will work. At all points in this workflow, when you move between items in the list output to the chat what workflow you are running and what step you are on. Maintain a checklist of the workflow steps you have completed and the steps you have not completed. 

1. Go to the planning/epics folder of the product repository. Confirm the existance of a folder named after the epic. Confirm existance of stories.md inside that folder.
2. Look at planning/BOARD.md and confirm that the epic hasn't already been implemented
<<<<<<< HEAD
3. Confirm you are on main branch.
4. Create a branch called epic/<epic-number>
5. Sync with Main: 
  * Run `git fetch origin main`.
  * Run `git merge origin/main` into the feature branch to ensure the feature is built on the latest code.
6. Run the /design-epic workflow until completion
7. Iterate through each of the stories in the epic. Do not stop between stories unless you need the user's input. Follow this loop for each story:
=======
3. Look in the epic folder and confirm the following files exist. If any of them do not, you MUST stop and remind the user to run the design-epic workflow first:
  * design.md
  * implementation.md
  * standards.md
  * stories.md
  * testing.md
4. Confirm you are on main branch. State this in the chat.
5. Create a branch called epic/<epic-number> off of the current branch. State the parent branch name in the chat.
6. Sync with Main: 
  * Run `git fetch origin main`.
  * Run `git merge origin/main` into the feature branch to ensure the feature is built on the latest code.
7. Iterate through each of the stories in the epic like this:
>>>>>>> 880c4c5 (Re-add .agent)
  * Run the /develop-story workflow for the story 
  * Run the /test workflow for the story
  * If any tests fail, run the /test-failure workflow for the first error. Then re-run the tests to see which tests failures remain - one fix for a failing test could fix other test failures too. There are NO circumstances where you should accept a test failure. If you cannot fix a test failure, stop and ask for help.
  * Mark the story implemented in stories.md
  * Commit the code with an appropriate commit message. Include the story and epic numbers in the commit message. 
<<<<<<< HEAD
8. Run the build and confirm it completes without error. If it does not and the cause is a failing test, run the /test-failure workflow as needed to fix it.
=======
8. Run the build (build-container.sh if there is web code and build-mobile.sh if there is mobile code) and confirm it completes without error. If it does not and the cause is a failing test, run the /test-failure workflow as needed to fix it.
>>>>>>> 880c4c5 (Re-add .agent)
9. Update planning/BOARD.md to indicate that the epic is now implemented.
10. Run `git push origin epic/<epic-number>`.
11. Execute the following command in a terminal: `notify-send epic-<epic-number> Implementation complete`  

Stop after these steps. Do not attempt to implement any other functionality.