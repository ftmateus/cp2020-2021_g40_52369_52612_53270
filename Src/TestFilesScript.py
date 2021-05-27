from TestsScriptBase import *

import os


PLOT_FILE = "mass_test"

all_test_files = get_test_files()

# layer_size = 111117
layer_size = 100

N_RUNS = 10


MAX_THREADS = os.cpu_count()

# samples = run_tests(layer_size, all_test_files, n_runs = 5)

#testing files individualy
#for test in all_test_files:
#    print("Using test file:", test)
#    run_tests(layer_size, [test], n_runs = N_RUNS)#
#

print("Using all test_01_* files")
run_tests(layer_size, get_test_files("test_01_*"), n_runs = N_RUNS)
#
#print("Using all test_02_* files")
#run_tests(layer_size, get_test_files("test_02_*"), n_runs = N_RUNS)

# print("Using all test_07_* files")
# run_tests(layer_size, get_test_files("test_07_*"), n_runs = N_RUNS)

print("Using all test_08_* files")
run_tests(layer_size, get_test_files("test_08_*"), n_runs = N_RUNS)


print("\033[0;32mTest complete!",)

os.remove(CSV_FILENAME)