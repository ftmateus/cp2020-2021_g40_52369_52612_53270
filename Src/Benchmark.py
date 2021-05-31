from TestsScriptBase import *
import os
import getopt
#################MAIN##################

opargs, args = getopt.getopt(sys.argv[1:], "h:l:")

layer_size = 1000000
threshold = 0.001
threads = [1, 2, 4, 8, 16, 32, 64]

tests = get_test_files("test_01_*")

for opt in opargs:
    if(opt[0] == "-l"):
        layer_size = int(opt[1])
    elif(opt[0] == "-h"):
        threshold = float(opt[1])

if(len(args) > 0):
    tests = args

if(layer_size <= 0):
    print("Specify valid layer size! (ex: -l 1000)")
    exit(1)

if(threshold <= 0.0):
    print("Specify valid threshold!")
    exit(1)

#all_test_files = get_test_files()

# samples = run_tests(layer_size, all_test_files, n_runs = 5)

# SEQsamples, OMPsamples = run_tests(layer_size, 
# ["test_files/test_09_a16-17_p3_w1", "test_files/test_07_a1M_p5k_w4"], n_runs = 5)

SEQSamples, OMPSamples = run_tests(layer_size, 
tests, n_runs = 5, threshold=threshold, threads=threads)

# SEQsamples, OMPsamples = run_tests(layer_size, 
# all_test_files, n_runs = 5)

export_results_stats(SEQSamples, OMPSamples, layer_size, threshold, threads)

print(GREEN + "Test complete!")

os.remove(CSV_FILENAME)