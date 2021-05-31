from TestsScriptBase import *

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

#nthreads (x) and time (y)
def plot_results_nthreads_time(plot_name, SEQStats, OMPStats):
    #plt.figure(figsize=(8,8), frameon=True)

    if(SEQStats.layer_size != OMPStats.layer_size):
        print(RED + "Layer size doesn't match!")
        return

    if(SEQStats.threshold != OMPStats.threshold):
        print(RED + "Threshold doesn't match!")
        return

    layer_size = SEQStats.layer_size
    threshold = SEQStats.threshold


    figure, (timesPlt, otherstatsPlt) = plt.subplots(2, figsize=(10,8))

    timesPlt.xaxis.set_major_locator(MaxNLocator(integer=True))

    otherstatsPlt.xaxis.set_major_locator(MaxNLocator(integer=True))

    timesPlt.set_title("Layer size: " + str(layer_size) + " Threshold: " + str(threshold))

    timesPlt.set_ylabel("Mean time (in seconds)")
    
    OMPxAxe = list(map(lambda t: " OMP-" + str(t), OMPStats.threads))    

    timesPlt.bar(["SEQ"], [SEQStats.meanTime[0]], color="red")

    timesPlt.bar(OMPxAxe, OMPStats.meanTime, color="blue")

    otherstatsPlt.set_xlabel("Number of Threads")

    otherstatsPlt.plot(OMPxAxe, OMPStats.speedUp, color='r', label = "SpeedUp")

    otherstatsPlt.plot(OMPxAxe, OMPStats.efficiency, color='g', label = "Efficiency")

    otherstatsPlt.plot(OMPxAxe, OMPStats.cost, color='b', label = "Cost")
    
    otherstatsPlt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          ncol=3, fancybox=True, shadow=True)

    plt.savefig(PLOTS_FOLDER + plot_name)
    plt.close()

##MAIN##

plot_name = sys.argv[1]

SEQStats = SamplesStats.import_from_csv_file(SEQ_STATS_OUT_FILE)

OMPStats = SamplesStats.import_from_csv_file(OMP_STATS_OUT_FILE)

plot_results_nthreads_time(plot_name, SEQStats, OMPStats)