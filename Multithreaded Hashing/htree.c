//Kristopher Pally
//3377.004
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <errno.h>     // for EINTR
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <string.h>
#include <math.h>

#include <sys/syscall.h>

#include "common.h"
#include "common_threads.h"


// Print out the usage of the program and exit.
void Usage(char*);
uint32_t jenkins_one_at_a_time_hash(const uint8_t* , uint64_t );

#define BSIZE 4096
uint32_t* htable;

int32_t numThreads = 0;
off_t nblocks = 0;
off_t bpthread = 0;
uint8_t* arr = 0;
off_t leftover = 0;

typedef struct bTree {
  int num;
  uint32_t hash;
  struct bTree* left;
  struct bTree* right;

} bTree;

// Initialize node to default values
void initTree(bTree *t, int nodeNum)
{
  t->num = nodeNum;
  t->hash = 0;
  t->left = NULL;
  t->right = NULL;
}

void* 
tree(void* root) 
{
  bTree* node = root;
  char convert[30];

  pthread_t c1 = 0;
  pthread_t c2 = 0;

  if (node->num < numThreads)
  {
    if ((node->num * 2) + 1 < numThreads) // create left child
    {
      bTree* child1 = malloc(sizeof(bTree));
      node->left = child1;
      initTree(child1, ((node->num * 2) + 1));
      Pthread_create(&c1, NULL, tree, node->left);
    }

    if ((node->num * 2) + 2 < numThreads) // create right child
    {
      bTree* child2 = malloc(sizeof(bTree));
      node->right = child2;
      initTree(child2, ((node->num * 2) + 2));
      Pthread_create(&c2, NULL, tree, node->right);
    }
  }

  if (node->num == (numThreads - 1) && leftover != 0) // case where there is leftover data to hash
    node->hash = jenkins_one_at_a_time_hash(&arr[(node->num) * bpthread * BSIZE], (bpthread * BSIZE) + leftover);
  else // hash block
    node->hash = jenkins_one_at_a_time_hash(&arr[(node->num) * bpthread * BSIZE], bpthread * BSIZE);

  // Wait for any children to complete so we can combine their hash later if necessary
  if(c1 != 0)
    Pthread_join(c1, NULL);
  if(c2 != 0)
    Pthread_join(c2, NULL);

  // Merge hashes and rehash if needed and store hash in convert
  if (node->right)
  {
    sprintf(convert, "%u%u%u", node->hash, node->left->hash, node->right->hash); // store hash and both child hashes in convert
    node->hash = jenkins_one_at_a_time_hash((uint8_t*)convert, strlen(convert)); // hash concatenated value
  }
  else if (node->left)
  {
    sprintf(convert, "%u%u", node->hash, node->left->hash); // store hash and left (only) child hash in convert
    node->hash = jenkins_one_at_a_time_hash((uint8_t*)convert, strlen(convert)); // hash concatenated value
  }
  
  return (void*) &(node->hash);
}

// Recursively deletes the binary tree
void deleteNode(bTree* root)
{
  if (!root)
    return;

  deleteNode(root->left);
  deleteNode(root->right);

  free(root);
}

int
main(int argc, char** argv)
{
  int32_t fd;
  struct stat buffer;
  uint32_t hash = 0;
  void* temp = NULL;

  bTree* root = malloc(sizeof(bTree));

  // input checking 
  if (argc != 3)
    Usage(argv[0]);

  // open input file
  fd = open(argv[1], O_RDWR);
  if (fd == -1) {
    perror("open failed");
    exit(EXIT_FAILURE);
  }

  numThreads = atoi(argv[2]);

  if (numThreads < 1)
  {
    printf("Please enter a number of threads greater than 0.\n");
    exit(EXIT_FAILURE);
  }
  
  // use fstat to get file size
  // calculate nblocks 
  if (fstat(fd, &buffer) == -1)
  {
    perror("fstat failed");
    exit(EXIT_FAILURE);
  }

  // check if the file can be evenly divided into BSIZE blocks, if not
  // allocate an extra block for the remainder
  if (buffer.st_size % BSIZE == 0)
    nblocks = buffer.st_size / BSIZE;
  else
    nblocks = (buffer.st_size / BSIZE) + 1;

  bpthread = nblocks / numThreads;

  // check if the number of blocks can be evenly divided into each thread, if not
  // save the remainder into the leftover variable
  if (nblocks % numThreads != 0)
    leftover = nblocks % numThreads;

  // calculate hash value of the input file
  arr = mmap(NULL, buffer.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
  if (arr == MAP_FAILED)
  {
    perror("mmap failed");
    exit(EXIT_FAILURE);
  }

  initTree(root, 0);
  pthread_t c1;

  double start = GetTime();
  Pthread_create(&c1, NULL, tree, root);
  Pthread_join(c1, &temp);
  hash = *(uint32_t*)temp;
  double end = GetTime();

  printf("hash value = %u \n", hash);
  printf("time taken = %f \n", (end - start));
  deleteNode(root);
  close(fd);
  return EXIT_SUCCESS;
}

uint32_t
jenkins_one_at_a_time_hash(const uint8_t* key, uint64_t length)
{
  uint64_t i = 0;
  uint32_t hash = 0;

  while (i != length) {
    hash += key[i++];
    hash += hash << 10;
    hash ^= hash >> 6;
  }
  hash += hash << 3;
  hash ^= hash >> 11;
  hash += hash << 15;
  return hash;
}

void
Usage(char* s)
{
  fprintf(stderr, "Usage: %s filename num_threads \n", s);
  exit(EXIT_FAILURE);
}
