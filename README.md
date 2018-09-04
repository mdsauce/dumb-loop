# Simple Bulk Tests
This will generate a random queue of tests.  The Queue will be consumed by a user defined number of worker threads that will run the test and report failures.

Run with `python <name of python file>.py`.  For example `$ python ios-test.py`.

### Utilities
To see the current number of tcp connections used by the threads  use `lsof -i | grep "python" | wc -l`.  This will grep for the python threads on the system and then count the lines.
