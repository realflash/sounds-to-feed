---
description: How to test after a change
---

These are the steps you should carry to test after any code chage that implements a story, tweak, or bug fix.  At all points in this workflow, when you move between items in the list output to the chat what workflow you are running and what step you are on. Maintain a checklist of the workflow steps you have completed and the steps you have not completed. 

  * Run these make targets. Only proceed to the next target if the previous target returns an exit code. If the exit code is non-zero or the test output includes warnings or errors consider this a test failure.
    * `make lint`
    * `make code-scan`
    * `make test-e2e`
    * `make test-e2e-system`