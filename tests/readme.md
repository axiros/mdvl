We visually inspect the test results.
If all ok we export record=1 and run again, so that we have the results
as the next set of assertions for the next run

Rationale: It is very tedious to write assertions with the escape codes and
change all the time when we add a new feature, which might cause a
re-arrrangement of the coloring in the code.

----

TO RECORD A NEW TEST RESULT SET: export record=1 - THEN RUN.')
to inspect before recording: export inspect=1 then run.

----
