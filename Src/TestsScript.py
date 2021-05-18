import subprocess
import os
import re
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

plt.style.use('default')

CSV_FILENAME = ".out.csv"

PLOTS_FOLDER = "plots/"

ENERGY_STORMS_OMP_EXEC = "./energy_storms_omp"
ENERGY_STORMS_SEQ_EXEC = "./energy_storms_seq"

MAX_THREADS = 8

class ProgramResultsSample:
    def __init__(self, layer_size, n_threads, test_files, time, results):
        self.time       = time
        self.layer_size = layer_size
        self.results    = results
        self.n_threads  = n_threads
        self.test_files = test_files

    def printAll(self):
        print("Time: ",         self.time)
        print("Layer size: ",   self.layer_size)
        print("Threads: ",      self.n_threads)
        print("Test files:\n",  self.test_files)
        print("Results:\n",     self.results)

    def compareResults(self, other):
        for i, r in enumerate(self.results):
            if r[1] != other.results[i][1]:
                return False
        
        return True

class SamplesStats:
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

        for i, s in enumerate(samples):
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

def start_energy_storms_program(layer_size, test_files, n_threads = 1):
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

        results = ProgramResultsSample(layer_size, n_threads, test_files, time, results)

        return results

    #FUNCTION START

    proc = subprocess.run([ENERGY_STORMS_OMP_EXEC, "-c", CSV_FILENAME, 
                    "-t", str(n_threads), str(layer_size)] + test_files)

    if proc.returncode != 0:
        print("Error while executing program! Aborting script...")
        exit(1)


    return parse_results()


#nthreads (x) and time (y)
def plot_results_nthreads_time(plot_name, samples, layer_size):
    #plt.figure(figsize=(8,8), frameon=True)

    x = np.arange(1, MAX_THREADS + 1)

    figure, (timesPlt, otherstatsPlt) = plt.subplots(2)

    # ax = times.figure().gca()
    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # ax = otherstats.figure().gca()
    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    stats = SamplesStats(samples)

    timesPlt.set_title("Layer size: " + str(layer_size))

    timesPlt.set_ylabel("Mean time (in seconds)")
    
    timesPlt.bar(x, stats.meanTime)

    otherstatsPlt.set_xlabel("Number of Threads")

    otherstatsPlt.plot(x, stats.speedUp, color='r', label = "SpeedUp")

    otherstatsPlt.plot(x, stats.efficiency, color='g', label = "Efficiency")

    otherstatsPlt.plot(x, stats.cost, color='b', label = "Cost")
    
    otherstatsPlt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
          ncol=3, fancybox=True, shadow=True)

    

    plt.savefig(PLOTS_FOLDER + plot_name)
    plt.close()

def run_tests(layer_size, test_files, n_runs = 2):
    samples = []

    for t in range (1, MAX_THREADS + 1):
        for _ in range(n_runs):
            samples.append(start_energy_storms_program(layer_size, test_files, n_threads=t))

    return samples

#################MAIN##################

all_test_files = get_test_files()

layer_size = 100

samples = run_tests(layer_size, all_test_files, n_runs = 10)

plot_results_nthreads_time("plot_init_arrays_speedup", samples, layer_size)

os.remove(CSV_FILENAME)





