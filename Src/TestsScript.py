import subprocess
import os
import re
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

plt.style.use('default')

CSV_FILENAME = ".out.csv"

PLOTS_FOLDER = "plots/"

ENERGY_STORMS_OMP_EXEC = "./energy_storms_omp"
ENERGY_STORMS_SEQ_EXEC = "./energy_storms_seq"

MAX_THREADS = os.cpu_count()# + 2

class ProgramResultsSample:
    def __init__(self, program, layer_size, n_threads, test_files, time, results):
        self.program    = program
        self.time       = time
        self.layer_size = layer_size
        self.results    = results
        self.n_threads  = n_threads
        self.test_files = test_files

    def printAll(self, towrite=sys.stdout):
        oldstdout = sys.stdout
        if(towrite != sys.stdout):
            sys.stdout = open(towrite, 'w')

        print("Program: ",      self.program)
        print("Time: ",         self.time)
        print("Layer size: ",   self.layer_size)
        print("Threads: ",      self.n_threads)
        print("Test files:\n")
        for t in self.test_files:
            print(t)
        print("Results:\n")
        for r in self.results:
            print(r[0], r[1])

        if(sys.stdout != oldstdout):
            sys.stdout.close()
            sys.stdout = oldstdout

    def compareResults(self, other):
        if self.layer_size != other.layer_size:
            return False
        for i, r in enumerate(self.results):
            if r[1] != other.results[i][1]:
                return False
        
        return True

class OMPSamplesStats:
    def __init__(self, samples):
        self.samples = samples
        self.meanTime = [0 for _ in range(MAX_THREADS)]
        self.speedUp = [0 for _ in range(MAX_THREADS)]
        self.efficiency = [0 for _ in range(MAX_THREADS)]
        self.cost = [0 for _ in range(MAX_THREADS)]
        self._computeMeanTime()
        self._computeSpeedup()
        self._computeEfficiency()
        self._computeCost()
    
    def _computeMeanTime(self):
        times = [[] for _ in range(MAX_THREADS)]

        for i, s in enumerate(self.samples):
            times[s.n_threads - 1].append(s.time)
            
        for i, tl in enumerate(times):
            if tl != []:
                self.meanTime[i] = np.mean(tl)
    
    def _computeSpeedup(self):
        assert len(self.speedUp) == len(self.meanTime)
        for t in range (0, len(self.meanTime)):
            self.speedUp[t] = self.meanTime[0]/self.meanTime[t]

    def _computeEfficiency(self):
        assert len(self.efficiency) == len(self.meanTime)
        for p in range (1, len(self.meanTime)):
            self.efficiency[p] = self.speedUp[p]/(p + 1)

    def _computeCost(self):
        assert len(self.cost) == len(self.meanTime)
        for p in range (0, len(self.meanTime)):
            self.cost[p] = (p + 1)*self.meanTime[p]


def get_test_files(regex_expr = "test_*"):
    test_files_folder = os.listdir("test_files/")

    regex = re.compile(regex_expr)

    test_files = []

    for path in test_files_folder:
        if regex.search(path):
            test_files.append("test_files/" + path)

    return test_files

def start_energy_storms_program(program, layer_size, test_files, n_threads = 1):
    def parse_results():
        output_arr = []
        with open(CSV_FILENAME, "r") as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                if(row != []):
                    output_arr.append(row)

            csv_file.close()

        time = float(output_arr[0][1])
        results = np.array(output_arr[2:])

        results = ProgramResultsSample(program, layer_size, n_threads, test_files, time, results)

        return results

    #FUNCTION START

    proc = None

    if(program == ENERGY_STORMS_OMP_EXEC):
        proc = subprocess.run([program, "-c", CSV_FILENAME, 
                            "-t", str(n_threads), str(layer_size)] + test_files)
    elif(program == ENERGY_STORMS_SEQ_EXEC):
        proc = subprocess.run([program, "-c", CSV_FILENAME, 
                            str(layer_size)] + test_files)
    else:
        assert False

    if proc.returncode != 0:
        print("\033[0;31mError while executing program! Aborting script...")
        os.remove(CSV_FILENAME)
        exit(1)


    return parse_results()


#nthreads (x) and time (y)
def plot_results_nthreads_time(plot_name, layer_size, SEQsamples = [], OMPsamples= []):
    #plt.figure(figsize=(8,8), frameon=True)

    figure, (timesPlt, otherstatsPlt) = plt.subplots(2)

    timesPlt.xaxis.set_major_locator(MaxNLocator(integer=True))

    otherstatsPlt.xaxis.set_major_locator(MaxNLocator(integer=True))

    stats = OMPSamplesStats(OMPsamples)

    timesPlt.set_title("Layer size: " + str(layer_size))

    timesPlt.set_ylabel("Mean time (in seconds)")
    
    SEQsamplesMeanTime = np.mean(list(map(lambda x: x.time, SEQsamples)))

    OMPxAxe = list(map(lambda x: " OMP-" + str(x),np.arange(1, MAX_THREADS + 1)))

    timesPlt.bar(["SEQ"], [SEQsamplesMeanTime], color="red")

    timesPlt.bar(OMPxAxe, stats.meanTime, color="blue")

    otherstatsPlt.set_xlabel("Number of Threads")

    otherstatsPlt.plot(OMPxAxe, stats.speedUp, color='r', label = "SpeedUp")

    otherstatsPlt.plot(OMPxAxe, stats.efficiency, color='g', label = "Efficiency")

    otherstatsPlt.plot(OMPxAxe, stats.cost, color='b', label = "Cost")
    
    otherstatsPlt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
          ncol=3, fancybox=True, shadow=True)

    plt.savefig(PLOTS_FOLDER + plot_name)
    plt.close()

def run_tests(layer_size, test_files, n_runs = 2):
    def _checkResults(newSample, lastSample):
        if(lastSample != None and not newSample.compareResults(lastSample)):
            print("\033[0;31mOutput mismatch! Differences:\033[0m")
            lastSample.printAll("Sample1_out.txt")
            newSample.printAll("Sample2_out.txt")
            subprocess.run(["diff", "Sample1_out.txt", "Sample2_out.txt"])
            os.remove(CSV_FILENAME)
            print("\033[0;31mAborting script...")
            exit(1)

    SEQsamples = []
    OMPsamples = []

    print("Testing original program")
    for r in range(n_runs):
        print( r + 1, "\r", end = '')
        newSample =  start_energy_storms_program(ENERGY_STORMS_SEQ_EXEC, layer_size, test_files)
        lastSample = None if SEQsamples == [] else SEQsamples[len(SEQsamples) - 1]
        _checkResults(newSample, lastSample)
        SEQsamples.append(newSample)

    print("Executing OMP program")
    for t in range (1, MAX_THREADS + 1):
        print(t, "thread(s)")
        for r in range(n_runs):
            print( r + 1, "\r", end = '')
            newSample =  start_energy_storms_program(ENERGY_STORMS_OMP_EXEC, layer_size, test_files, n_threads=t)
            lastSample = SEQsamples[len(SEQsamples) - 1] if OMPsamples == [] else OMPsamples[len(OMPsamples) - 1]
            _checkResults(newSample, lastSample)
            OMPsamples.append(newSample)
            
    return SEQsamples, OMPsamples

#################MAIN##################

all_test_files = get_test_files()

layer_size = 100000000

# samples = run_tests(layer_size, all_test_files, n_runs = 5)

SEQsamples, OMPsamples = run_tests(layer_size, 
["test_files/test_09_a16-17_p3_w1"], n_runs = 1)

plot_results_nthreads_time("plot_init_arrays_speedup", layer_size, SEQsamples, OMPsamples)

print("\033[0;32mTest complete!")

os.remove(CSV_FILENAME)