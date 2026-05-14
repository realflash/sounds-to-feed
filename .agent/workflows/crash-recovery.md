---
description: Recovering from Antigravity failure
---

Another agent was in the middle of implementing a user story implementation, bug fix, or tweak and crashed. I am unable to recover the conversation. You are required to carry on where the crashed agent left off.

1. Enumerate the code repositories in this workspace. "product_standards" is a repository for guiding the design process, "infrastructure3" is a repository that provides the declaritive configuration for the production environment that this product runs in (and shoul generally be read only as far as you are concerned), and the third repository is the product we are working on.
2. Find out what branch name is checked out in the product repo. 
  - If it is main, we were probably not in the middle of anything and you should check with the user what to do next. 
  - If it is epic-xxx, we were implementing stories. Review planning/epic_xxx/stories.md and determine what has been implemented, and what hasn't, largely by reviewing the git history of the branch and un-committed changes. Determine which step in the workflow /implement-epic the agent had last completed. 
  - If it is bug-xxx, look up the description of the bug in planning/BOARD.md and assess where the agent was in fixing it, largely by reviewing the git history of the branch and un-committed changes. Determine which step in the workflow /fix-bug the agent had last completed.
  - If it is tweak-xxx, look up the description of the tweak in planning/BOARD.md and assess where the agent was in fixing it, largely by reviewing the git history of the branch and un-committed changes. Determine which step in the workflow /implement-epic-tweak the agent had last completed.
3. Tell the user what you think the agent was working on, which workflow step number it got to, and make a plan for completing the task.
4. Stop here and allow the user to review the plan, then continue the incomplet workflow with the next numbered step.