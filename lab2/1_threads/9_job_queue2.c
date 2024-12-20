/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <malloc.h>
#include <pthread.h>

struct job {
  /* Link field for linked list.  */
  struct job* next; 
  char *message;
  /* Other fields describing work to be done... */
};

/* A linked list of pending jobs.  */
struct job* job_queue;

void process_job (struct job* tmp){
  char print_me[20];
  printf("Thread %ld completed job %s \n", pthread_self(), tmp->message);
}

/* A mutex protecting job_queue.  */
pthread_mutex_t job_queue_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (1) {
    struct job* next_job;

    /* Lock the mutex on the job queue.  */
    pthread_mutex_lock (&job_queue_mutex);
    /* Now it's safe to check if the queue is empty.  */
    if (job_queue == NULL)
      next_job = NULL;
    else {
      /* Get the next available job.  */
      next_job = job_queue;
      /* Remove this job from the list.  */
      job_queue = job_queue->next;
    }
    /* Unlock the mutex on the job queue, since we're done with the
       queue for now.  */
    pthread_mutex_unlock (&job_queue_mutex);

    /* Was the queue empty?  If so, end the thread.  */
    if (next_job == NULL)
      break;

    /* Carry out the work.  */
    process_job (next_job);
    /* Clean up.  */
    free (next_job);
  }
  return NULL;
}


int main(void){
  struct job *one   = (struct job *) malloc(sizeof(struct job));
  struct job *two   = (struct job *) malloc(sizeof(struct job));
  struct job *three = (struct job *) malloc(sizeof(struct job));

  one->message   = "1";
  two->message   = "2";
  three->message = "3";

  job_queue = (struct job *) malloc(sizeof(struct job));
  job_queue->message = "4";
  job_queue->next = three;

  three->next = two;
  two->next = one;
  one->next = NULL;


  pthread_t first;
  pthread_t second;

  pthread_create(&first, NULL, thread_function, NULL);
  pthread_create(&second, NULL, thread_function, NULL);

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
