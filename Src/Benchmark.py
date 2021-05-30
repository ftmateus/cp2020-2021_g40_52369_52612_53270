from TestsScriptBase import *

import os
#################MAIN##################

PLOT_FILE = sys.argv[1]

all_test_files = get_test_files()

layer_size = 10000000

threshold= 0.001

# samples = run_tests(layer_size, all_test_files, n_runs = 5)

# SEQsamples, OMPsamples = run_tests(layer_size, 
# ["test_files/test_09_a16-17_p3_w1", "test_files/test_07_a1M_p5k_w4"], n_runs = 5)

SEQsamples, OMPsamples = run_tests(layer_size, 
get_test_files("test_01_*"), n_runs = 2, threshold=threshold)

# SEQsamples, OMPsamples = run_tests(layer_size, 
# all_test_files, n_runs = 5)

export_samples_summary(SEQsamples, "seq_samples", layer_size, 
    threshold, ENERGY_STORMS_SEQ_EXEC, [1])
#plot_results_nthreads_time(PLOT_FILE, layer_size, threshold, SEQsamples, OMPsamples)

print("\033[0;32mTest complete! Plot saved on file", PLOT_FILE)

os.remove(CSV_FILENAME)