---
description: How to deal with a test failure
---

# Test failure

Carry out these steps if you are carrying out this workflow because a test failed.  At all points in this workflow, when you move between items in the list output to the chat what workflow you are running and what step you are on. Maintain a checklist of the workflow steps you have completed and the steps you have not completed. 

1. Assess the error output of the test. You are quite slow at using a browser. Determine if it would be faster to modify the test or increased the testing error level or simply look at the code and try to guess the problem rather than reproducing it with a browser.
2. Take the step that you have deemed fastest and attempt to find the source of the problem. if you don't come to a conclusion easily use the other diagnosis methods.
3. Fix the problem.
4. Re-run the test that failed. Continue to fix and test until the test passes. 
5. Commit your changes.