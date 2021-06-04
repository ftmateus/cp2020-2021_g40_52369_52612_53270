from TestsScriptBase import *
import getopt

opargs, args = getopt.getopt(sys.argv[1:], "t:l:h:")

n_threads = 1
layer_size = 0
threshold = 0.001

for opt in opargs:
    if(opt[0] == "-t"):
        n_threads = int(opt[1])
    elif(opt[0] == "-l"):
        layer_size = int(opt[1])
    elif(opt[0] == "-h"):
        threshold = float(opt[1])

if(layer_size <= 0):
    print("Specify valid layer size! (ex: -l 1000)")
    exit(1)

if(n_threads <= 0):
    print("Specify valid threads number! (ex: -l 1000)")
    exit(1)

if(threshold <= 0.0):
    print("Specify valid threshold!")
    exit(1)

test_files = args

print("Running original program")
seqSample = start_energy_storms_program(ENERGY_STORMS_SEQ_EXEC,
                layer_size, test_files, threshold=threshold)

print("Running OMP program")
ompSample = start_energy_storms_program(ENERGY_STORMS_OMP_EXEC,
                layer_size, test_files, n_threads, threshold=threshold)

resultMatch = seqSample.compareResults(ompSample)

if(resultMatch):
    print(GREEN + "Result match!" )
else:
    print(RED + "Result mismatch! Differences:" + DEFAULT_COLOR)
    seqSample.printAll("Sample1_out.txt")
    ompSample.printAll("Sample2_out.txt")
    subprocess.run(["diff", "Sample1_out.txt", "Sample2_out.txt"])

#os.remove(CSV_FILENAME)