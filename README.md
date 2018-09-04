# Simple Bulk Tests
This will generate a random queue of tests.  The Queue will be consumed by a user defined number of worker threads that will run the test and report failures.

Run with `python <name of python file>.py`.  For example `$ python ios-test.py`.

### Updating Number of Tests or Concurrency
Edit the two values at the top of the file: 
`THREADLIMIT = 50`
`TESTS = 1500`

THREADLIMIT is the number of threads (concurrent number of tests).  TESTS is the total number of tests you'd like to start.

### Utilities
To see the current number of tcp connections used by the threads  use `lsof -i | grep "python" | wc -l`.  This will grep for the python threads on the system and then count the lines.
