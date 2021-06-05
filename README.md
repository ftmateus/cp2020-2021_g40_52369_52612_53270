# Simplified simulation of high-energy particle storms

### EduHPC 2018: Peachy assignment

(c) 2018 Arturo Gonzalez-Escribano, Eduardo Rodriguez-Gutiez
Group Trasgo, Universidad de Valladolid (Spain)

--------------------------------------------------------------

This is a version of the assignment customized by [João Lourenço](https://docentes.fct.unl.pt/joao-lourenco),
to be used in the course  of Concurrency and Parallelism at [FCT-NOVA](www.di.fct.unl.pt), 
edition 2020-21.

--------------------------------------------------------------

Read the handout and use the sequential code as reference to study.
Use the other source files to parallelize with the proper programming model.

Edit the first lines in the Makefile to set your preferred compilers and flags
for both the sequential code and for each parallel programming model: 
OpenMP, MPI, and CUDA.

To see a description of the Makefile options execute:
`$ make help`

Use the input files in the test_files directory for your first tests.
Students are encouraged to manually write or automatically generate
their own input files for more complete tests. See a description of
the input files format in the handout.

--------------------------------------------------------------


    \item \verb|BuildPlot.py| - Produces a plot with the metrics about the \verb|Benchmark.py| results. The script imports the \verb|seq.csv| and \verb|omp.csv| files produced by the \verb|Benchmark.py| script and uses the Matplotlib python module to produce the plot.   

In order to test and benchmark our solution, we implemented and used some python scripts for this effect:

-TestScriptBase.py
    Is considered the base of the other scripts and contains all functions and variables necessary for the other scripts to run. The script has no effect by itself, and needs to be imported by the other scripts.

-Benchmark.py
    like the file name implies, is used to benchmark our solution. After the benchmark, the script will export the results metrics (mean time, speedup, efficiency, cost, etc...) to the seq.csv| and omp.csv files, which contains the metrics about the sequential (energy_storms_seq) and paralleled (energy_storms_omp) programs samples metrics, respectively.
    
    To use this script execute:
    `$ python3 Benchmark.py -h (threshold) -l (layer_size) (tests)+`

-RunCompare.py
    Used to test the paralleled version of the program with a specific number of threads by comparing the results with the original, sequential program. The script will run both programs once.

    To use this script execute:
    `$ python3 RunCompare.py -t (threads) -l (layer_size) -h (threshold) (tests)+`

-TestFilesScript.py
    Tests all test files individually and combined (example: test all test\02 files) in order to check the correctness of the paralleled program.     

    To use this script execute:
    `$ python3 TestFilesScript.py`

-BuildPlot.py
    Produces a plot with the metrics about the (Benchmark.py) results. The script imports the (seq.csv) and (omp.csv) files produced by the (Benchmark.py) script and uses the Matplotlib python module to produce the plot.   

    To use this script execute:
    `$ python3 BuildPlot.py (plot_name)`