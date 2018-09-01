# Simple Bulk Tests
This will generate a random queue of tests.  The Queue will be consumed by a user defined number of worker threads that will run the test and report failures.

### Utilities
To see the current number of tcp threads open use `lsof -i | grep "python" | wc -l`.  This will grep for the python threads on the system and then count the lines.