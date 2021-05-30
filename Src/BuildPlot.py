from TestsScriptBase import *

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

#nthreads (x) and time (y)
def plot_results_nthreads_time(plot_name, layer_size, threshold, SEQsamples = [], OMPsamples= []):
    #plt.figure(figsize=(8,8), frameon=True)

    figure, (timesPlt, otherstatsPlt) = plt.subplots(2, figsize=(10,8))

    timesPlt.xaxis.set_major_locator(MaxNLocator(integer=True))

    otherstatsPlt.xaxis.set_major_locator(MaxNLocator(integer=True))

    stats = OMPSamplesStats(OMPsamples)

    timesPlt.set_title("Layer size: " + str(layer_size) + " Threshold: " + str(threshold))

    timesPlt.set_ylabel("Mean time (in seconds)")
    
    SEQsamplesMeanTime = mean(list(map(lambda x: x.time, SEQsamples)))

    OMPxAxe = list(map(lambda x: " OMP-" + str(x), range(1, MAX_THREADS + 1)))

    timesPlt.bar(["SEQ"], [SEQsamplesMeanTime], color="red")

    timesPlt.bar(OMPxAxe, stats.meanTime, color="blue")

    otherstatsPlt.set_xlabel("Number of Threads")

    otherstatsPlt.plot(OMPxAxe, stats.speedUp, color='r', label = "SpeedUp")

    otherstatsPlt.plot(OMPxAxe, stats.efficiency, color='g', label = "Efficiency")

    otherstatsPlt.plot(OMPxAxe, stats.cost, color='b', label = "Cost")
    
    otherstatsPlt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          ncol=3, fancybox=True, shadow=True)

    plt.savefig(PLOTS_FOLDER + plot_name)
    plt.close()
