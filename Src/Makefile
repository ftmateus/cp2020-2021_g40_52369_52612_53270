#
# Simplified simulation of high-energy particle storms
#
# Parallel computing (Degree in Computer Engineering)
# 2017/2018
#
# EduHPC 2018: Peachy assignment
#
# (c) 2018 Arturo Gonzalez-Escribano, Eduardo Rodriguez-Gutiez
# Grupo Trasgo, Universidad de Valladolid (Spain)
#
# This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.
# https://creativecommons.org/licenses/by-sa/4.0/
#
#
# The current Parallel Computing course includes contests using:
# OpenMP, MPI, and CUDA.
#

# Compilers
CC=gcc
MPICC=mpicc
CUDACC=nvcc
OMPFLAG=-fopenmp

# Flags for optimization and libs
FLAGS=-O3
LIBS=-lm

# Targets to build
EXES=energy_storms_seq energy_storms_omp
EXES_NO_ASSERTIONS=energy_storms_seq_no_assert energy_storms_omp_no_assert

# Rules. By default show help
help:
	@echo
	@echo "Simplified simulation of high-energy particle storms"
	@echo
	@echo "Group Trasgo, Universidad de Valladolid (Spain)"
	@echo "EduHPC 2018: Peachy assignment"
	@echo "Modified by João Lourenço, NOVA University Lisbon"
	@echo
	@echo "make energy_storms_seq	Build only the sequential version"
	@echo "make energy_storms_omp	Build only the OpenMP version"
	@echo
	@echo "make all	Build all versions (Sequential, OpenMPCUDA)"
	@echo "make debug_seq	Build the sequential version with demo output for small arrays (size<=35)"
	@echo "make debug_par	Build the parallel version with demo output for small arrays (size<=35)"
	@echo "make clean	Remove the targets"
	@echo

all: $(EXES)

all_no_assert: $(EXES_NO_ASSERTIONS)

energy_storms_seq: energy_storms.c
	$(CC) $(CFLAGS) $(DEBUG) $(NOASSERT) -o $@ $< $(LIBS)

energy_storms_seq_no_assert:
	$(CC) $(CFLAGS) -DNDEBUG $(DEBUG) -o energy_storms_seq energy_storms.c $< $(LIBS)

energy_storms_omp: energy_storms_omp.c
	$(CC) $(CFLAGS) $(DEBUG) $(NOASSERT) $(OMPFLAG) -o $@ $< $(LIBS)

energy_storms_omp_no_assert:
	$(CC) $(CFLAGS) -DNDEBUG $(DEBUG) $(OMPFLAG) -o energy_storms_omp energy_storms_omp.c $< $(LIBS)

# Remove the target files
clean:
	rm -rf $(EXES)

# Compile in debug mode
debug_seq:
	make energy_storms_seq DEBUG=-DDEBUG

debug_omp:
	make energy_storms_omp DEBUG=-DDEBUG

	
# debug_omp_benchmark_layer_init:
# 	make debug_omp BENCHMARK_LAYER_INIT=-DBENCHMARK_LAYER_INIT
