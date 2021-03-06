/*
 * Simplified simulation of high-energy particle storms
 *
 * Parallel computing (Degree in Computer Engineering)
 * 2017/2018
 *
 * Version: 2.0
 *
 * OpenMP code.
 *
 * (c) 2018 Arturo Gonzalez-Escribano, Eduardo Rodriguez-Gutiez
 * Grupo Trasgo, Universidad de Valladolid (Spain)
 *
 * This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.
 * https://creativecommons.org/licenses/by-sa/4.0/
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <sys/time.h>
#include <omp.h>
#include <assert.h>

#define DEFAULT_COLOR   "\033[0m"
#define RED             "\033[0;31m"
#define GREEN           "\033[0;32m"
#define YELLOW          "\033[0;33m"
#define BLUE            "\033[0;34m"
#define PURPLE          "\033[0;35m"
#define CYAN            "\033[0;36m"
#define WHITE           "\033[0;37m"

#define MIN_PARALLEL_THRESHOLD 1000

typedef enum
{
	FALSE, TRUE
} boolean;


#define printfColor(color, format, ...) \
    {\
        if(isatty(fileno(stdout))) \
            printf(format, ##__VA_ARGS__); \
        else \
            printf(format, ##__VA_ARGS__);\
    }

void setColor(char *color)
{
	if (isatty(fileno(stdout)))
		printf("%s", color);
}

/* Function to get wall time */
double cp_Wtime()
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return tv.tv_sec + 1.0e-6 * tv.tv_usec;
}

typedef float energy_t;

double threshold = 0.001f;

/**
 * define this symbol to check if a bug is caused by the new implementation
 * of the energy relaxation
 */
#undef ENERGY_RELAXATION_BEFORE
#undef ENERGY_BOMBARDMENT_BEFORE

/* Structure used to store data for one storm of particles */
typedef struct
{
	int size;    // Number of particles
	int *posval; // Positions and values
} Storm;

/* THIS FUNCTION CAN BE MODIFIED */
/* Function to update a single position of the layer */
void update(energy_t *layer, int layer_size, int k, int pos, energy_t energy)
{
	/* 1. Compute the absolute value of the distance between the
	 impact position and the k-th position of the layer */
	int distance = pos - k;
	if (distance < 0)
		distance = -distance;

	/* 2. Impact cell has a distance value of 1 */
	distance = distance + 1;

	/* 3. Square root of the distance */
	/* NOTE: Real world atenuation typically depends on the square of the distance.
	 We use here a tailored equation that affects a much wider range of cells */
	float atenuacion = sqrtf((float) distance);
	/* 4. Compute attenuated energy */
	energy_t energy_k = energy / layer_size / atenuacion;

	
	#ifndef ENERGY_BOMBARDMENT_BEFORE
	/* 
	 * Since the range where the absolute value is higher than the threshold
	 * is determined a priori on the new implementation of the energy bombardment, 
	 * this assertion should not fail
	 */
	assert(energy_k >= threshold / layer_size || energy_k <= -threshold / layer_size);
	#else 
	if(energy_k >= threshold / layer_size || energy_k <= -threshold / layer_size)
	#endif
		layer[k] = layer[k] + energy_k;
}

/* ANCILLARY FUNCTIONS: These are not called from the code section which is measured, leave untouched */
/* DEBUG function: Prints the layer status */
void debug_print(int layer_size, energy_t *layer, int *positions,
		energy_t *maximum, int num_storms, Storm *storms)
{
	unsigned int i, k;

	//https://www.lix.polytechnique.fr/~liberti/public/computing/prog/c/C/FUNCTIONS/format.html
	int k_justify = (int) log10(layer_size) + 1;

	/* Only print for array size up to 35 (change it for bigger sizes if needed) */

	if (layer_size <= 35)
	{
		/* Traverse layer */
		for (k = 0; k < layer_size; k++)
		{
			/* Print the energy value of the current cell */
			printf("%0*d | ", k_justify, k);

			printf("%10.4f |", layer[k]);

			/* Compute the number of characters.
			 This number is normalized, the maximum level is depicted with 60 characters */
			int ticks = (int) (60 * layer[k] / maximum[num_storms - 1]);

			/* Print all characters except the last one */
			setColor(PURPLE);
			for (i = 0; i < ticks - 1; i++)
				printf("o");

			/* If the cell is a local maximum print a special trailing character */
			if (k > 0 && k < layer_size - 1 && layer[k] > layer[k - 1]
					&& layer[k] > layer[k + 1])
				printfColor(RED, "x")
			else
				printf("o");

			setColor(DEFAULT_COLOR);

			/* If the cell is the maximum of any storm, print the storm mark */
			for (i = 0; i < num_storms; i++)
				if (positions[i] == k)
					printfColor(GREEN, " M%d", i);

			/* Line feed */
			printf("\n");
		}
	}
}

/*
 * Function: Read data of particle storms from a file
 */
Storm read_storm_file(char *fname)
{
	FILE *fstorm = fopen(fname, "r");
	if (fstorm == NULL)
	{
		fprintf(stderr, "Error: Opening storm file %s\n", fname);
		exit(EXIT_FAILURE);
	}

	Storm storm;
	int ok = fscanf(fstorm, "%d", &(storm.size));
	if (ok != 1)
	{
		fprintf(stderr, "Error: Reading size of storm file %s\n", fname);
		exit(EXIT_FAILURE);
	}

	storm.posval = (int *) malloc(sizeof(int) * storm.size * 2);
	if (storm.posval == NULL)
	{
		fprintf(stderr,
				"Error: Allocating memory for storm file %s, with size %d\n",
				fname, storm.size);
		exit(EXIT_FAILURE);
	}

	int elem;
	for (elem = 0; elem < storm.size; elem++)
	{
		ok = fscanf(fstorm, "%d %d\n", &(storm.posval[elem * 2]),
				&(storm.posval[elem * 2 + 1]));
		if (ok != 2)
		{
			fprintf(stderr, "Error: Reading element %d in storm file %s\n",
					elem, fname);
			exit(EXIT_FAILURE);
		}
	}
	fclose(fstorm);

	return storm;
}

boolean csv = FALSE;

short n_threads = 1;

short processOptions(int argc, char *argv[])
{
	short optargc = 0;
	char c;
	while ((c = getopt(argc, argv, "c:t:h:")) != -1)
	{
		switch (c)
		{
			case 'c': case 'C':
				csv = TRUE;
				if (optarg != NULL)
				{
					FILE *f = freopen(optarg, "w", stdout);
					assert(f != NULL);
					optargc++;
				}
				break;
			case 't': case 'T':
			{
				n_threads = atoi(optarg);

				//omp_set_num_threads(n_threads);
				optargc++;
				break;
			}
			case 'h': case 'H':
			{
				threshold = atof(optarg);

				optargc++;
				break;
			}
		}
		optargc++;
	}
	return optargc;
}

#ifndef ENERGY_RELAXATION_BEFORE
void energy_relaxation(energy_t *layer, int layer_size)
{
	int offset = (layer_size - 2) / omp_get_num_threads();

	int firstCellIndex = offset*omp_get_thread_num() + 1;
	int endCellIndex = firstCellIndex + offset - 1;

	if (omp_get_thread_num() == omp_get_num_threads() - 1)
	{
		/**
		 * The last thread will iterate the remainder additional 
		 * points
		 */
		assert(endCellIndex <= layer_size - 2);

		endCellIndex += (layer_size - 2) - endCellIndex;

		assert(endCellIndex == layer_size - 2);
	}

	energy_t *cellBeforeFirstCell = &layer[firstCellIndex - 1];
	energy_t *cellAfterEndCell = &layer[endCellIndex + 1];

	energy_t oldCellAfterEndCellValue = *cellAfterEndCell;
	energy_t nextOldPreviousCellValue = *cellBeforeFirstCell;

	/**
	 *	The threads should wait for each other in order to get 
	 *  the old values of the layer array before those values are
	 *  destroyed.
	 */
	#pragma omp barrier

	int k = firstCellIndex;
	for (; k <= endCellIndex; k++)
	{
		energy_t oldCurrentCellValue = layer[k];

		if (&layer[k + 1] == cellAfterEndCell)
			layer[k] = (nextOldPreviousCellValue + layer[k] + oldCellAfterEndCellValue) / 3;
		else
			layer[k] = (nextOldPreviousCellValue + layer[k] + layer[k + 1]) / 3;

		nextOldPreviousCellValue = oldCurrentCellValue;
	}

	assert(k == endCellIndex + 1);
	assert(&layer[k] == cellAfterEndCell);
}
#endif

/*
 * MAIN PROGRAM
 */
int main(int argc, char *argv[])
{
	n_threads = omp_get_max_threads();

	short optargc = processOptions(argc, argv);

	if (n_threads <= 0)
	{
		fprintf(stderr, "Invalid number of threads! %d\n", n_threads);
		exit(EXIT_FAILURE);
	}

	if (threshold <= 0.0)
	{
		fprintf(stderr, "Invalid threshold! %f\n", threshold);
		exit(EXIT_FAILURE);
	}

	/* 1.1. Read arguments */
	if (argc - optargc < 3)
	{
		fprintf(stderr,
				"Usage: %s <options> <size> <storm_1_file> [ <storm_i_file> ] ... \n",
				argv[0]);
		exit(EXIT_FAILURE);
	}

	int layer_size = atoi(argv[optargc + 1]);
	int num_storms = argc - optargc - 2;
	Storm storms[num_storms];

	/* 1.2. Read storms information */
	for (int i = 2 + optargc; i < argc; i++)
		storms[i - (2 + optargc)] = read_storm_file(argv[i]);

	/* 1.3. Intialize maximum levels to zero */
	energy_t maximum[num_storms];
	int positions[num_storms];
	for (int i = 0; i < num_storms; i++)
	{
		maximum[i] = 0.0f;
		positions[i] = 0;
	}

	/* 2. Begin time measurement */
	double ttotal = cp_Wtime();

	/* START: Do NOT optimize/parallelize the code of the main program above this point */

	/* 3. Allocate memory for the layer and initialize to zero */
	energy_t *layer = (energy_t *) malloc(sizeof(energy_t) * layer_size);

	#ifdef ENERGY_RELAXATION_BEFORE
	energy_t *layer_copy = (energy_t *) malloc(sizeof(energy_t) * layer_size);
	#endif

	if (layer == NULL)
	{
		fprintf(stderr, "Error: Allocating the layer memory\n");
		exit(EXIT_FAILURE);
	}

	#pragma omp parallel num_threads(n_threads) if(n_threads > 1)
	{
		#pragma omp for simd
		for (int kk = 0; kk < layer_size; kk++)
		{
			layer[kk] = 0.0f;

			#ifdef ENERGY_RELAXATION_BEFORE
			layer_copy[kk] = 0.00f;
			#endif
		}
	}

	/**
	 * The range that all particles affected in 
	 * the layer array.
	 */
	#ifndef ENERGY_BOMBARDMENT_BEFORE
	int maxL = 0, minL = layer_size;
	#else
	int maxL = layer_size, minL = 0;
	#endif
	/* 4. Storms simulation */
	for (int i = 0; i < num_storms; i++)
	{
		int position = 0;
		/**
		 * The range that a particle will affect in the layer array 
		 */
		int maxP = layer_size, minP = 0;

		energy_t energy;
		#pragma omp parallel num_threads(n_threads) if(n_threads > 1 && layer_size > MIN_PARALLEL_THRESHOLD)
		{
			/* 4.1. Add impacts energies to layer cells */
			/* For each particle */
			for (int j = 0; j < storms[i].size; j++)
			{
				#pragma omp single
				{
					/* Get impact energy (expressed in thousandths) */
					energy = (energy_t) storms[i].posval[j * 2 + 1] * 1000;
					/* Get impact position */
					position = storms[i].posval[j * 2];

					#ifndef ENERGY_BOMBARDMENT_BEFORE

					long double atenuation = energy / threshold;
					unsigned long long distanceMax = (unsigned long long) atenuation*atenuation;

					//check overflow
					if(atenuation > 1.0 && distanceMax == 0)
						distanceMax = layer_size;

					//to avoid underflow, since distanceMax is an unsigned type
					if(distanceMax > 0)
						distanceMax--;

					//to avoid overflows/undeflows
					maxP = distanceMax >= layer_size ? layer_size : position + distanceMax;
					minP = distanceMax >= position ? 0 : position - distanceMax;

					/**
					 * maxP and minP can be out of bounds
					 */
					maxP = maxP >= layer_size ? layer_size : maxP;
					minP = minP >= layer_size ? layer_size : minP;

					maxL = maxP > maxL ? maxP : maxL;
					minL = minP < minL ? minP : minL;

					//fprintf(stderr, "%d, %d, %d, %d, %llu\n", maxL, minL, maxP, minP, distanceMax);

					assert(maxL >= minL);
					assert(maxL >= maxP && minL <= minP);
					assert(minL <= layer_size && minL >= 0);
					assert(maxL <= layer_size && maxL >= 0);
					assert(maxP <= layer_size && maxP >= 0);
					assert(minP <= layer_size && minP >= 0);

					#endif
				}

				/* For each cell in the layer */
				/* 4.2.2. Update layer using the ancillary values.
				Skip updating the first and last positions */
				#pragma omp for
				for (int k = minP; k < maxP; k++)
				{
					/* Update the energy value for the cell */
					update(layer, layer_size, k, position, energy);
				}
			}

				/* 4.2. Energy relaxation between storms */
			#ifndef ENERGY_RELAXATION_BEFORE //code below is after

				int interval = maxL - minL;
				assert(interval >= 0);
				assert(minL + interval <= layer_size);
				if(interval > 0)
					energy_relaxation(&layer[minL], interval);

			#else //code below is before
				/* 4.2.1. Copy values to the ancillary array */
				#pragma omp for
				for (int k = 0; k < layer_size; k++)
					layer_copy[k] = layer[k];

				/* 4.2.2. Update layer using the ancillary values.
				Skip updating the first and last positions */
				#pragma omp for
				for (int k = 1; k < layer_size - 1; k++)
					layer[k] = (layer_copy[k - 1] + layer_copy[k] + layer_copy[k + 1])
							/ 3;

			#endif

			/* 4.3. Locate the maximum value in the layer, and its position */
			int maxk = minL;
			#pragma omp for nowait
			for (int k = minL + 1; k < maxL - 1; k++)
			{
				/* Check it only if it is a local maximum */
				if (layer[k] > layer[k - 1] && layer[k] > layer[k + 1])
				{
					if (layer[k] > layer[maxk])
					{
						maxk = k;
					}
				}
			}

			/**
			 * The energy values on the layer can be always rising 
			 * or always falling
			 */
			if(maxk != minL)
				maxk = layer[maxL] > layer[minL] ? maxL : minL;

			#pragma omp critical
			{
				if (layer[maxk] > maximum[i])
				{
					maximum[i] = layer[maxk];
					positions[i] = maxk;
				}
			}

			#pragma omp single
			{
				free(storms[i].posval);
			}
		}
	}
	/* END: Do NOT optimize/parallelize the code below this point */

	/* 5. End time measurement */
	ttotal = cp_Wtime() - ttotal;

	/* 6. DEBUG: Plot the result (only for layers up to 35 points) */
	#ifdef DEBUG
	if(!csv)
		debug_print( layer_size, layer, positions, maximum, num_storms, storms);
	#endif

	/* 7. Results output, used by the Tablon online judge software */
	printf("\n");

	char *separator = csv ? "," : " ";
	/* 7.1. Total computation time */
	printfColor(BLUE, "Time:%s", separator)
	printf("%lf\n", ttotal);
	/* 7.2. Print the maximum levels */
	printfColor(BLUE, "Results:\n")

	for (int i = 0; i < num_storms; i++)
		printf("%d%s%f\n", positions[i], separator, maximum[i]);
	printf("\n");

	free(layer);

	#ifdef ENERGY_RELAXATION_BEFORE
	free(layer_copy);
	#endif

	/**
	 * The stdout can be a csv file
	 */
	fclose(stdout);

	/* 9. Program ended successfully */
	return 0;
}
