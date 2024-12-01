//Kristopher Pally
//3377.004

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>


#define MAX_HISTORY 100
#define MAX_CHAR 1024

typedef struct {
	char history[MAX_HISTORY][MAX_CHAR];
	int head, tail, num_entries;
} queue;

// Initializes the queue to starting position
void initHistory(queue *q)
{
	q->num_entries = 0;
	q->head = 0;
	q->tail = 0;
}

// Prints contents of history, starting from head position
// and printing num_entries elements in the history
void printQueue(queue *q)
{
	int i = 0;
	int pos = q->head;

	while (i < q->num_entries)
	{
		printf("%d %s", i, q->history[pos]);
		pos = (pos + 1) % MAX_HISTORY;

		i++;
	}
}

// Removes entry at the head of the queue, decrements num_entries, and moves head forward
// until it reaches the end of the array and then loops back to the start of the array
int dequeue(queue *q)
{
	// If the queue is empty, reinitialize the values and return -1
	// to signal that all entries were removed
	if (q->num_entries == 0)
	{
		q->head = 0;
		q->tail = 0;
		return -1;
	}

	q->num_entries--;
	q->head = (q->head + 1) % MAX_HISTORY;

	return 1;
}

// Copies the command passed in to the history array, increments num_entries
// and moves the tail forward by 1 until it reaches the end of the array and
// then loops back to the start of the array
int enqueue(queue *q, char *h)
{
	strcpy(q->history[q->tail], h);
	q->num_entries++;
	q->tail = (q->tail + 1) % MAX_HISTORY;

	return 1;
}

// Returns the command in history array at the given offset
char* getQueue(queue *q, int offset)
{
	return (q->history[(q->head + offset) % MAX_HISTORY]);
}

// Executes a single command when there is no piping to be done
void executeSingle(char** args)
{
	pid_t cpid1 = fork();
	if (cpid1 < 0)
	{
		perror("fork failed");
		exit(EXIT_FAILURE);
	}

	if (cpid1 == 0) // child path
	{
		execvp(args[0], args);
		perror("Single exec failed");
		exit(EXIT_FAILURE);
	}
	waitpid(cpid1, NULL, 0);
	return;
}

// Executes multiple commands when there are pipes
void executeMulti(char* args)
{
	char *myargs[MAX_CHAR];
	char *command, *arg, *brks, *brkw;
	int commandCount, argCount;
	int fd[2];
	int prevPipe = dup(STDIN_FILENO); // duplicates STDIN_FILENO to prevPipe to avoid closing STDIN_FILENO

	commandCount = 0;
	// Separate input into larger command chunks delimited by pipes
	for(command = strtok_r(args, "|", &brks); command; command = strtok_r(NULL, "|", &brks))
	{
		commandCount++;

		// Check if input is empty or we're done reading input,
		// if so then exit function
		if (strcmp(command, "\n") == 0)
			return;

		// remove leading whitespace by moving the pointer for command 
		while (command[0] == ' ')
			command++;

		// Set flag that we're at the final command if > 1 command was input
		// or set flag that only 1 command was input
		if (command[strlen(command) - 1] == '\n' && commandCount > 1)
			commandCount = -1;
		else if (command[strlen(command) - 1] == '\n' && commandCount == 1)
			commandCount = -2;
		
		// Remove the newline character at the end of the input
		if (command[strlen(command) - 1] == '\n')
			command[strlen(command) - 1] = '\0';

		// Set the first argument as the command to be called and
		// reset the argument counter to 0
		myargs[0] = command;
		argCount = 0;

		// Separate command into it's arguments and place them into myargs array
		for(arg = strtok_r(command, " ", &brkw); arg; arg = strtok_r(NULL, " ", &brkw))
		{
			if (argCount > 0)
				myargs[argCount] = arg;
			argCount++;
		}
		// Set the element after the last argument to be NULL
		myargs[argCount] = NULL;

		if(pipe(fd) == -1)
			perror("pipe failed");
		
		// Create a child process for the current command to be executed
		pid_t cpid1 = fork();
		if (cpid1 < 0)
		{
			perror("fork failed");
			exit(EXIT_FAILURE);
		}

		if (cpid1 == 0) // child path
		{
			// If prevPipe is not equal to STDIN_FILENO, it's connected to the previous pipe
			// so we need to change STDIN_FILENO to point to the pipe
			if(prevPipe != STDIN_FILENO)
			{
				if (dup2(prevPipe, STDIN_FILENO) < 0)
					perror("perror w/ prevPipe");
				close(prevPipe);
			}

			// If we're at the final command, simply execute the last command
			if (commandCount == -1)
			{
				execvp(myargs[0], myargs);
				perror("Multi exec failed");
				exit(EXIT_FAILURE);
			}
			// Otherwise, redirect STDOUT to the pipe for further use
			else
			{
				if (dup2(fd[1], STDOUT_FILENO) < 0)
					perror("Error piping");
				close(fd[1]);

				execvp(myargs[0], myargs);
				perror("Multi exec failed");
				exit(EXIT_FAILURE);
			}
		}
		else // parent path
		{
			waitpid(cpid1, NULL, 0); // Wait for child to finish

			// If we're at the last command, close all pipe connections and return
			if (commandCount == -1) 
			{
				close(fd[0]);
				close(fd[1]);
				close(prevPipe);
				return;
			}
			// Otherwise, close the read end of the previous pipe and write end
			// of the current pipe and set prevPipe to the read end of the current pipe
			else
			{
				close(prevPipe);
				close(fd[1]);
				prevPipe = fd[0];
			}
		}
	}
	return;
}

int main()
{
	size_t buffer = 0;
	char *myargs[MAX_CHAR];
	char *line = NULL;
	char *tempStr = NULL;
	char toQueue[MAX_CHAR];
	char *command, *arg, *brks, *brkw;
	int commandCount, argCount;
	int isRepeat = 0;
	queue q;
	initHistory(&q);

	myargs[MAX_CHAR - 1] = NULL;
	printf("sish> ");
	while(1)
	{
		// reset input, buffer, and isRepeat before reading input
		
		line = NULL;
		buffer = 0;
		isRepeat = 0;

		// use getline() to get the input string and store unmodified version in
		// toQueue and tempStr for later queuing
		getline(&line, &buffer, stdin);
		tempStr = strdup(line);

		repeat: // label used for (history [offset])
		strcpy(toQueue, line);

		// Reset number of sentences to 0
		commandCount = 0;

		// Separate input into larger command chunks delimited by pipes
		for(command = strtok_r(line, "|", &brks); command; command = strtok_r(NULL, "|", &brks))
		{
			commandCount++;

			// Check if input is empty or we're done reading input,
			// if so then reprompt the shell command
			if (strcmp(command, "\n") == 0)
				break;

			// remove leading whitespace by moving the pointer for command 
			while (command[0] == ' ')
				command++;

			// Set flag that we're at the final command if >1 command was input
			// or set flag that only 1 command was input
			if (command[strlen(command) - 1] == '\n' && commandCount > 1)
				commandCount = -1;
			else if (command[strlen(command) - 1] == '\n' && commandCount == 1)
				commandCount = -2;

			// Set the first argument as the command to be called and
			// reset the argument counter to 0
			myargs[0] = command;
			argCount = 0;

			// Remove the newline character at the end of the input
			if (command[strlen(command) - 1] == '\n')
				command[strlen(command) - 1] = '\0';


			// Separate command into it's arguments and place them into myargs array
			for(arg = strtok_r(command, " ", &brkw); arg; arg = strtok_r(NULL, " ", &brkw))
			{
				if (argCount > 0)
					myargs[argCount] = arg;
				argCount++;
			}
			// Set the element after the last argument to be NULL
			myargs[argCount] = NULL;

			// Built-in exit command
			if (strcmp(myargs[0], "exit") == 0)
			{	
				// Free memory allocated by strdup and exit
				free(line);
				free(tempStr);
				exit(EXIT_SUCCESS);
			}
			// Built-in cd command
			else if (strcmp(myargs[0], "cd") == 0)
			{	
				if (chdir(myargs[1]) < 0)
				{
					perror("Could not change directories");
				}
				break;
			}
			// Built-in history command
			else if (strcmp(myargs[0], "history") == 0) 
			{
				if (argCount > 1) // Checks if arguments were passed
				{
					if (strcmp(myargs[1], "-c") == 0) // Clear history
					{
						// Call dequeue until history is empty
						while (dequeue(&q) > 0){}
						isRepeat = 2; // Set to 2 to avoid adding command
					}
					else // history [offset]
					{
						int i = atoi(myargs[1]);

						// Checks if second argument is a number
						if (strcmp(myargs[1], "0") != 0 && i == 0)
						{
							printf("Invalid argument\n");
							break;
						}
						// Checks if the offset is valid, if it is then copy the command from
						// history to line and jump to repeat label for reexecution
						if (i > q.num_entries - 1)
						{
							printf("history not available\n");
							break;
						}
						// Free memory allocated for line before reallocating more with strdup
						free(line);
						line = strdup(getQueue(&q, i));
						isRepeat = 1; // Set to 1 to avoid re-adding command
						goto repeat;
					}
					break;
				}
				else
				{
					// If history has 100 entries, remove the oldest entry
					if (q.num_entries == MAX_HISTORY)
					{
						dequeue(&q);
					}
					// add history call to queue and print the queue
					if (enqueue(&q, toQueue) < 0)
					{
						perror("failed to queue");
					}
					printQueue(&q);
					isRepeat = 2; // Set to 2 to avoid re-adding command
					break;
				}
			}

			// If a single command was input, call executeSingle with command
			if (commandCount == -2) 
			{
				executeSingle(myargs);
				break;
			}
			// If multiple commands were input, call executeMulti with the unmodified input
			else if (commandCount == -1) 
			{
				if (isRepeat == 0)
				{
					if (enqueue(&q, toQueue) < 0)
						perror("failed to queue");
					isRepeat = 2; // Set to 2 to avoid re-adding command
				}
				executeMulti(toQueue);
				break;
			}
			
		}
		if (isRepeat == 0)
		{
			// If history has 100 entries, remove the oldest entry
			if (q.num_entries == MAX_HISTORY)
			{
				dequeue(&q);
			}
			// Adds command to the history if it is not a reexecution
			if (enqueue(&q, toQueue) < 0)
				perror("failed to queue");
		}
		else if (isRepeat == 1)
		{
			// If history has 100 entries, remove the oldest entry
			if (q.num_entries == MAX_HISTORY)
			{
				dequeue(&q);
			}
			// Adds history [offset] command to queue if reexecution
			if (enqueue(&q, tempStr) < 0)
				perror("failed to queue");
		}
		// Free memory allocated for tempStr and line before looping the shell prompt
		free(tempStr);
		free(line);
		printf("sish> ");
	}

	exit(EXIT_FAILURE);
}
