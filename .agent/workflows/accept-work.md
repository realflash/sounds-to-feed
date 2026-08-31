---
description: How to implement an epic
---

If you fail at any point and suspect you may lose data, stop and ask for help.

1. Look at planning/BOARD.md and compare to the branch name. Make sure you know what epic or bugfix or tweak you are working on.
2. Make sure all a changes are committed to the current branch. 
3. **Identify Parent Branch**: Run `git reflog | grep "checkout: moving from .* to $(git rev-parse --abbrev-ref HEAD)" | head -n1` to definitively identify the branch from which current work was branched. State this parent branch name in the chat. DO NOT ASSUME IT IS MAIN.
4. Merge the current branch into the parent branch. DO NOT MERGE ANY FURTHER. If the parent was an epic branch, you MUST NOT merge that into main.
5. Switch to the parent branch and delete the local branch you just merged, and its remote counterpart.
6. Push the parent branch to the remote repository.

Stop after these steps. Do not attempt to implement any other functionality.