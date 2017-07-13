# Test Strategy

Recorded output per test case in the results folder.

After changes we do:

    export record=1; ./test_mdvl.py

and the test results will be overwritten.

We can then, after some optical inspection of the output also use git diff to
inspect deviations to the previous results and judge if they are expected from
the change.

Again: We visually inspect the test results.
If all ok we export record=1 and run again, so that we have the results
as the next set of assertions for the next run

Rationale: It is very tedious to write assertions with the escape codes and
change all the time when we add a new feature, which might cause a
re-arrrangement of the coloring in the code.


If there are exceptions we can also set

    export inspect=1; ./test_mdv.py

-> no asssertion checking then, just outputting renderings.
