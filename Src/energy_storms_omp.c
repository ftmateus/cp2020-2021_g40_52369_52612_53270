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
#include<stdio.h>
#include<stdlib.h>
#include <unistd.h>
#include<math.h>
#include<sys/time.h>
#include<omp.h>

#define DEFAULT_COLOR   "\033[0m"
#define RED             "\033[0;31m"
#define GREEN           "\033[0;32m"
#define YELLOW          "\033[0;33m"
#define BLUE            "\033[0;34m"
#define PURPLE          "\033[0;35m"
#define CYAN            "\033[0;36m"
#define WHITE           "\033[0;37m"

#define printfColor(color, format, ...) \
    {\
        if(isatty(fileno(stdout))) \
            printf(color format DEFAULT_COLOR, ##__VA_ARGS__); \
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

#define THRESHOLD    0.001f

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


	/* 5. Do not add if its absolute value is lower than the threshold */
	if (energy_k >= THRESHOLD / layer_size
			|| energy_k <= -THRESHOLD / layer_size)
		layer[k] = layer[k] + energy_k;
	else
	{
		//if(k>pos) stop cycle return 0;
	}
	//if the energy decreases below the threshold, then it's not worth to do more
}

/* ANCILLARY FUNCTIONS: These are not called from the code section which is measured, leave untouched */
/* DEBUG function: Prints the layer status */
void debug_print(int layer_size, energy_t *layer, int *positions,
		energy_t *maximum, int num_storms, Storm *storms)
{
	int i, k;

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
			//TODO number particles
			// {
			//     int particles_hit = 0;
			//     for(int j=0; i< num_storms; j++)
			//     {
			//         particles_hit += storms[j].posval[2*k];
			//     }
			//     if(particles_hit > 0)
			//     {
			//         printfColor(RED, "%d |", particles_hit)
			//     }
			//     else
			//     {
			//         printf("%d |", particles_hit);
			//     }
			// }
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

/*
 * MAIN PROGRAM
 */
int main(int argc, char *argv[])
{
	int i, j, k;

	/* 1.1. Read arguments */
	if (argc < 3)
	{
		fprintf(stderr,
				"Usage: %s <size> <storm_1_file> [ <storm_i_file> ] ... \n",
				argv[0]);
		exit(EXIT_FAILURE);
	}

	int layer_size = atoi(argv[1]);
	int num_storms = argc - 2;
	Storm storms[num_storms];

	/* 1.2. Read storms information */
	for (i = 2; i < argc; i++)
		storms[i - 2] = read_storm_file(argv[i]);

	/* 1.3. Intialize maximum levels to zero */
	energy_t maximum[num_storms];
	int positions[num_storms];
	for (i = 0; i < num_storms; i++)
	{
		maximum[i] = 0.0f;
		positions[i] = 0;
	}

	/* 2. Begin time measurement */
	double ttotal = cp_Wtime();

	/* START: Do NOT optimize/parallelize the code of the main program above this point */

	/* 3. Allocate memory for the layer and initialize to zero */
	energy_t *layer = (energy_t *) malloc(sizeof(energy_t) * layer_size);

	if (layer == NULL || layer_copy == NULL)
	{
		fprintf(stderr, "Error: Allocating the layer memory\n");
		exit(EXIT_FAILURE);
	}
	double initial = cp_Wtime();

#pragma omp parallel for
	for (int kk = 0; kk < layer_size; kk++)
	{
		layer[kk] = 0.0f;
	}

	double final = cp_Wtime();


	/* 4. Storms simulation */
	for (i = 0; i < num_storms; i++)
	{

		/* 4.1. Add impacts energies to layer cells */
		/* For each particle */
		//O(p)
		for (j = 0; j < storms[i].size; j++)
		{
			/* Get impact energy (expressed in thousandths) */
			energy_t energy = (energy_t) storms[i].posval[j * 2 + 1] * 1000;
			/* Get impact position */
			int position = storms[i].posval[j * 2];

			/* For each cell in the layer */
			//o(l)
			//atenuation = energy/layer_size/THRESHOLD
				//atenuation*atenuation = distanceMax
				//if(pos+distanceMax>layer_size) max = layer_size-1 else max = pos+distanceMax
				//if(pos-distanceMax<0) min = 0 else min = pos-distanceMax
#pragma omp paralell for
			for (k = 0; k < layer_size; k++)
			{

				/* Update the energy value for the cell */
				update(layer, layer_size, k, position, energy);
			}
		}

		//total = O(p*(l/t))
		/* 4.2. Energy relaxation between storms */
		/* 4.2.1. Copy values to the ancillary array */

		int previousNeighbor = 0;
		int LastNeighbor=100;
		/* 4.2.2. Update layer using the ancillary values.
		 Skip updating the first and last positions */

#pragma omp paralell for private(previousNeighbor)
		for (k = 1; k < layer_size - 1; k++)//TODO k not =1, depending on thread
		//TODO nextPreviousNeighbor = layer[k-1] wouldn't work, because a thread might end before another starts
		{
			int nextPreviousNeighbor = layer[k];

			layer[k] = (previousNeighbor + layer[k] + layer[k + 1]) / 3;//layer[k+1] doesn't work for last element of layer in thread
			previousNeighbor = nextPreviousNeighbor;

			if (layer[k] > maximum[i])
			{
				maximum[i] = layer[k];
				positions[i] = k;
			}
		}
		//layer[k] = (previousNeighbor + layer[k] + layer[last) / 3;
		/* 4.3. Locate the maximum value in the layer, and its position */

	}

	/* END: Do NOT optimize/parallelize the code below this point */

	/* 5. End time measurement */
	ttotal = cp_Wtime() - ttotal;

	/* 6. DEBUG: Plot the result (only for layers up to 35 points) */
#ifdef DEBUG
    debug_print( layer_size, layer, positions, maximum, num_storms, storms);
    #endif

	/* 7. Results output, used by the Tablon online judge software */
	printf("\n");
	/* 7.1. Total computation time */
	printfColor(BLUE, "Time: ")
	printf("%lf\n", ttotal);
	/* 7.2. Print the maximum levels */
	printfColor(BLUE, "Results:\n")
	for (i = 0; i < num_storms; i++)
		printf("%d %f\n", positions[i], maximum[i]);
	printf("\n");

	/* 8. Free resources */
	for (i = 0; i < argc - 2; i++)
		free(storms[i].posval);

	/* 9. Program ended successfully */
	return 0;
}

