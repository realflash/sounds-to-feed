---
description: How to fix a bug
---

There are two top level folders in this workspace. One is called product_standards, and it should not be modified unless the user's prompt explicitly tells you to do so. The other is the repository containing the code for the product. This is where you will work. At all points in this workflow, when you move between items in the list output to the chat what workflow you are running and what step you are on.

# Existing bug

If the user tells you that you have not successfully fixed an existing bug, or that an existing bug has returned, run these steps.

1. Make sure that you are clear what the bug ID is that user says is not fixed. If the user says something like "not fixed" immediately after you tell them a bug is fixed, assume the last bug you were working on.
2. Assess the user's report. 
 - If the user has told you to look at the browser, they have left it on a page showing an error. Look at the content of that page to determine the syptoms.
 - If the user has provided an image, it is probably a screenshot of the error. Assess the content of the image.
 - If the user has provided a video, it is probably a video of the error ocurring. Assess the content of the image.
3. Change the status of the bug in planning/BOARD.md as BUG-<ID> back to unfixed.
4. Reproduce the bug yourself.
5. Assess whether you have enough information about the scenario in which the bug occurred to have a reasonable guess at the cause. Consider whether it would be faster to ask the user for more information than have multiple guesses.
6. If a bugfix branch for this bug exists, switch to it. Otherwise, note your current branch and create a new bugfix branch bug/<ID> off of it. State the parent branch name in the chat.
7. Sync with Main: 
  * Run `git fetch origin main`.
  * Run `git merge origin/main` into the feature branch to ensure the feature is built on the latest code.
8. The build the user is testing must have previously passed all existing tests in order to have been deployed to user testing. The fact that the bug is still present means that test coverage is insufficient. Write a new playwright test which invokes the bug and fails or update an existing test if you think that is more appropriate. You will have to determine whether it should be a system test or a mocked test.
9. Now run the /test-failure workflow.
10. Bump the last component of the semver VERSION file for the component(s) you have modified
11. Confirm that ./build_container.sh completes without error for the component(s) you have modified. If it does not, attempt to fix it and continue running it unil it does complete without error.
12. Execute the following command in a terminal: `notify-send bug-<ID> Bug fix ready for UAT`  
13. Update planning/BOARD.md to indicate that the bug is now fixed.
14. Run `git push origin bug/<ID>`.
15. Execute the following command in a terminal: `notify-send bug-<ID> Bug fixed`  

Stop after these steps. Do not attempt to implement any other functionality.



# New bug

Run these steps if the user does not say that an existing bug is not fixed.

1. Assess the user's report. 
 - If the user has told you to look at the browser, they have left it on a page showing an error. Look at the content of that page to determine the syptoms.
 - If the user has provided an image, it is probably a screenshot of the error. Assess the content of the image.
 - If the user has provided a video, it is probably a video of the error ocurring. Assess the content of the image.
2. Generate a ten-digit unique ID for the bug based on the ISO UTC datetime it was reported like YYMMDDHHMM.
3. Log the bug in planning/BOARD.md as BUG-<ID> and give it a short description
4. Assess whether you have enough information about the scenario in which the bug occurred to have a reasonable guess at the cause. Consider whether it would be faster to ask the user for more information than have multiple guesses.
5. Note your current branch and create a new bugfix branch bug/<ID> off of it. State the parent branch name in the chat.
6. Sync with Main: 
  * Run `git fetch origin main`.
  * Run `git merge origin/main` into the feature branch to ensure the feature is built on the latest code.
7. The build the user is testing must have previously passed all existing tests in order to have been deployed to user testing. The fact that they have found a bug means that test coverage is insufficient. Write a new playwright test which invokes the bug and fails. You will have to determine whether it should be a system test or a mocked test.
8. Now run the /test-failure workflow.
10. Confirm that ./build.sh completes without error. If it does not, attempt to fix it and continue running it unil it does complete without error.
9. Update planning/BOARD.md to indicate that the bug is now fixed.
10. Run `git push origin bug/<ID>`.
11. Execute the following command in a terminal: `notify-send bug-<ID> Bug fixed`  

Stop after these steps. Do not attempt to implement any other functionality.