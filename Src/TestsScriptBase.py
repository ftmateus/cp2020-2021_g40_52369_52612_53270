import subprocess
import os
import re
import sys
import csv
import signal

from statistics import mean

DEFAULT_COLOR   = "\033[0m"
RED             = "\033[0;31m"
GREEN           = "\033[0;32m"
YELLOW          = "\033[0;33m"
BLUE            = "\033[0;34m"
PURPLE          = "\033[0;35m"
CYAN            = "\033[0;36m"
WHITE           = "\033[0;37m"

CSV_FILENAME = ".out.csv"

PLOTS_FOLDER = "plots/"

ENERGY_STORMS_OMP_EXEC = "./energy_storms_omp"
ENERGY_STORMS_SEQ_EXEC = "./energy_storms_seq"

SEQ_STATS_OUT_FILE = "seq.csv"
OMP_STATS_OUT_FILE = "omp.csv"

#MAX_THREADS = os.cpu_count()

class ProgramResultsSample:
    def __init__(self, program, layer_size, n_threads, test_files, time, results, threshold):
        self.program    = program
        self.time       = time
        self.threshold  = threshold
        self.layer_size = layer_size
        self.results    = results
        self.n_threads  = n_threads
        self.test_files = test_files
        self.stderr_out = None

    def printAll(self, towrite=sys.stdout):
        oldstdout = sys.stdout
        if(towrite != sys.stdout):
            sys.stdout = open(towrite, 'w')

        print("Program: ",      self.program)
        print("Time: ",         self.time)
        print("Layer size: ",   self.layer_size)
        print("Threshold: ",    self.threshold)
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

class SamplesStats:
    def __init__(self, samples, program, layer_size, threshold, threads):
        assert(len(threads) > 0)
        assert(threads[0] == 1)
        for i, t in enumerate(threads):
            if(i > 0):
                assert(threads[i] > threads[i - 1])
        self.program = program
        self.layer_size = layer_size
        self.threshold = threshold
        self.threads = threads
        self.meanTime = [0 for _ in range(len(threads))]
        self.speedUp = [0 for _ in range(len(threads))]
        self.efficiency = [0 for _ in range(len(threads))]
        self.cost = [0 for _ in range(len(threads))]
        self._computeMeanTime(samples)
        self._computeSpeedup()
        self._computeEfficiency()
        self._computeCost()
    
    def _computeMeanTime(self, samples):
        times = [[] for _ in range(len(self.threads))]

        for i, s in enumerate(samples):
            times[self.threads.index(s.n_threads)].append(s.time)
            
        for i, tl in enumerate(times):
            if tl != []:
                self.meanTime[i] = mean(tl)
    
    def _computeSpeedup(self):
        assert len(self.speedUp) == len(self.meanTime)
        for t in range (0, len(self.meanTime)):
            self.speedUp[t] = self.meanTime[0]/self.meanTime[t]

    def _computeEfficiency(self):
        assert len(self.efficiency) == len(self.meanTime)
        for p in range (1, len(self.meanTime)):
            self.efficiency[p] = self.speedUp[p]/(self.threads[p] + 1)

    def _computeCost(self):
        assert len(self.cost) == len(self.meanTime)
        for p in range (0, len(self.meanTime)):
            self.cost[p] = (self.threads[p] + 1)*self.meanTime[p]

    def export_to_csv_file(self, file_name):
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["program", str(self.program)])
            writer.writerow(["layer_size", str(self.layer_size)])
            writer.writerow(["threshold", str(self.threshold)])
            writer.writerow([])
            writer.writerow(["n_threads", "mean_time", "speed_up", "efficiency", "cost"])
            for i, t in enumerate(self.threads):
                writer.writerow([str(t), str(self.meanTime[i]), str(self.speedUp[i]), 
                    str(self.efficiency[i]), str(self.cost[i])])


    @classmethod
    def import_from_csv_file(cls, file_name):
        obj = cls.__new__(cls)  # Does not call __init__
        super(SamplesStats, obj).__init__()  # Don't forget to call any polymorphic base class initializers
        
        with open(file_name, "r") as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            readerArr = []
            for row in reader:
                if(row != []):
                    readerArr.append(row)

            csv_file.close()
            obj.program = readerArr[0][1]
            obj.layer_size = readerArr[1][1]
            obj.threshold = readerArr[2][1]
            obj.threads = []
            obj.meanTime = []
            obj.speedUp = []
            obj.efficiency = []
            obj.cost = []

            for i in range (4, len(readerArr)):
                threads = int(readerArr[i][0])
                obj.threads.append(threads)
                meanTime = float(readerArr[i][1])
                obj.meanTime.append(meanTime)
                speedUp = float(readerArr[i][2])
                obj.speedUp.append(speedUp)
                efficiency = float(readerArr[i][3])
                obj.efficiency.append(efficiency)
                cost = float(readerArr[i][4])
                obj.cost.append(cost)

        return obj

def get_test_files(regex_expr = "test_*"):
    test_files_folder = os.listdir("test_files/")

    regex = re.compile(regex_expr)

    test_files = []

    for path in test_files_folder:
        if regex.search(path):
            test_files.append("test_files/" + path)

    return test_files

def start_energy_storms_program(program, layer_size, test_files, n_threads = 1, threshold=0.001):
    def parse_results():
        output_arr = []
        with open(CSV_FILENAME, "r") as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                if(row != []):
                    output_arr.append(row)

            csv_file.close()

        time = float(output_arr[0][1])
        results = output_arr[2:]

        results = ProgramResultsSample(program, layer_size, n_threads, test_files, time, results, threshold)

        return results

    #FUNCTION START

    proc = None

    if(program == ENERGY_STORMS_OMP_EXEC):
        proc = subprocess.run([program, "-c", CSV_FILENAME, "-h", str(threshold),
                            "-t", str(n_threads), str(layer_size)] + test_files)
    elif(program == ENERGY_STORMS_SEQ_EXEC):
        proc = subprocess.run([program, "-c", CSV_FILENAME, "-h", str(threshold), 
                            str(layer_size)] + test_files)
    else:
        assert False

    if proc.returncode != 0:
        print(RED + "Error while executing",program, "! Error code:", proc.returncode ,"Aborting script..." + DEFAULT_COLOR)
        subprocess.run(["cat", CSV_FILENAME])
        os.remove(CSV_FILENAME)
        exit(1)


    return parse_results()

def run_tests(layer_size, test_files, n_runs = 2, 
    test_original_program = True, threshold=0.001,
    threads=range(1, os.cpu_count() + 1)):

    def _checkResults(newSample, lastSample):
        if(lastSample != None and not newSample.compareResults(lastSample)):
            print(RED + "Output mismatch! Differences:" + DEFAULT_COLOR)
            lastSample.printAll("Sample1_out.txt")
            newSample.printAll("Sample2_out.txt")
            subprocess.run(["diff", "Sample1_out.txt", "Sample2_out.txt"])
            os.remove(CSV_FILENAME)
            print(RED + "Aborting script..." + DEFAULT_COLOR)
            exit(1)

    SEQsamples = []
    OMPsamples = []

    newSample = None
    lastSample = None

    if(test_original_program):
        print("Testing original program")
        for r in range(n_runs):
            print( r + 1, "\r", end = '')
            newSample =  start_energy_storms_program(ENERGY_STORMS_SEQ_EXEC, layer_size, test_files, threshold=threshold)
            _checkResults(newSample, lastSample)
            SEQsamples.append(newSample)
            lastSample = newSample

        

    print("Testing OMP program")
    for t in threads:
        print(BLUE + str(t) + " thread(s)" + DEFAULT_COLOR)
        for r in range(n_runs):
            print( r + 1, "\r", end = '')
            newSample =  start_energy_storms_program(ENERGY_STORMS_OMP_EXEC, layer_size, test_files, n_threads=t, threshold=threshold)
            _checkResults(newSample, lastSample)
            OMPsamples.append(newSample)
            lastSample = newSample
            
    return SEQsamples, OMPsamples

def export_results_stats(SEQSamples, OMPSamples, layer_size, threshold, threads):
    SEQStats = SamplesStats(SEQSamples, ENERGY_STORMS_SEQ_EXEC, layer_size, threshold, [1])

    OMPStats = SamplesStats(OMPSamples, ENERGY_STORMS_OMP_EXEC, layer_size, threshold, threads)

    SEQStats.export_to_csv_file(SEQ_STATS_OUT_FILE)
    OMPStats.export_to_csv_file(OMP_STATS_OUT_FILE)
        

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)