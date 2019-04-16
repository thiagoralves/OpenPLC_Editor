/**
 * Linux specific code
 **/

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>
#include <pthread.h>
#include <locale.h>
#include <semaphore.h>

static sem_t Run_PLC;

long AtomicCompareExchange(long* atomicvar,long compared, long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}
long long AtomicCompareExchange64(long long* atomicvar, long long compared, long long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}

void PLC_GetTime(IEC_TIME *CURRENT_TIME)
{
    struct timespec tmp;
    clock_gettime(CLOCK_REALTIME, &tmp);
    CURRENT_TIME->tv_sec = tmp.tv_sec;
    CURRENT_TIME->tv_nsec = tmp.tv_nsec;
}

void PLC_timer_notify(sigval_t val)
{
    PLC_GetTime(&__CURRENT_TIME);
    sem_post(&Run_PLC);
}

timer_t PLC_timer;

void PLC_SetTimer(unsigned long long next, unsigned long long period)
{
    struct itimerspec timerValues;
	/*
	printf("SetTimer(%lld,%lld)\n",next, period);
	*/
    memset (&timerValues, 0, sizeof (struct itimerspec));
	{
#ifdef __lldiv_t_defined
		lldiv_t nxt_div = lldiv(next, 1000000000);
		lldiv_t period_div = lldiv(period, 1000000000);
	    timerValues.it_value.tv_sec = nxt_div.quot;
	    timerValues.it_value.tv_nsec = nxt_div.rem;
	    timerValues.it_interval.tv_sec = period_div.quot;
	    timerValues.it_interval.tv_nsec = period_div.rem;
#else
	    timerValues.it_value.tv_sec = next / 1000000000;
	    timerValues.it_value.tv_nsec = next % 1000000000;
	    timerValues.it_interval.tv_sec = period / 1000000000;
	    timerValues.it_interval.tv_nsec = period % 1000000000;
#endif
	}
    timer_settime (PLC_timer, 0, &timerValues, NULL);
}
//
void catch_signal(int sig)
{
//  signal(SIGTERM, catch_signal);
  signal(SIGINT, catch_signal);
  printf("Got Signal %d\n",sig);
  exit(0);
}


static unsigned long __debug_tick;

pthread_t PLC_thread;
static pthread_mutex_t python_wait_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t python_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t debug_wait_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t debug_mutex = PTHREAD_MUTEX_INITIALIZER;

int PLC_shutdown = 0;

int ForceSaveRetainReq(void) {
    return PLC_shutdown;
}

void PLC_thread_proc(void *arg)
{
    while (!PLC_shutdown) {
        sem_wait(&Run_PLC);
        __run();
    }
    pthread_exit(0);
}

#define maxval(a,b) ((a>b)?a:b)
int startPLC(int argc,char **argv)
{
    struct sigevent sigev;
    setlocale(LC_NUMERIC, "C");

    PLC_shutdown = 0;

    sem_init(&Run_PLC, 0, 0);

    pthread_create(&PLC_thread, NULL, (void*) &PLC_thread_proc, NULL);

    memset (&sigev, 0, sizeof (struct sigevent));
    sigev.sigev_value.sival_int = 0;
    sigev.sigev_notify = SIGEV_THREAD;
    sigev.sigev_notify_attributes = NULL;
    sigev.sigev_notify_function = PLC_timer_notify;

    pthread_mutex_init(&debug_wait_mutex, NULL);
    pthread_mutex_init(&debug_mutex, NULL);
    pthread_mutex_init(&python_wait_mutex, NULL);
    pthread_mutex_init(&python_mutex, NULL);

    pthread_mutex_lock(&debug_wait_mutex);
    pthread_mutex_lock(&python_wait_mutex);

    timer_create (CLOCK_MONOTONIC, &sigev, &PLC_timer);
    if(  __init(argc,argv) == 0 ){
        PLC_SetTimer(common_ticktime__,common_ticktime__);

        /* install signal handler for manual break */
        signal(SIGINT, catch_signal);
    }else{
        return 1;
    }
    return 0;
}

int TryEnterDebugSection(void)
{
    if (pthread_mutex_trylock(&debug_mutex) == 0){
        /* Only enter if debug active */
        if(__DEBUG){
            return 1;
        }
        pthread_mutex_unlock(&debug_mutex);
    }
    return 0;
}

void LeaveDebugSection(void)
{
    pthread_mutex_unlock(&debug_mutex);
}

int stopPLC()
{
    /* Stop the PLC */
    PLC_shutdown = 1;
    sem_post(&Run_PLC);
    PLC_SetTimer(0,0);
	pthread_join(PLC_thread, NULL);
	sem_destroy(&Run_PLC);
    timer_delete (PLC_timer);
    __cleanup();
    pthread_mutex_destroy(&debug_wait_mutex);
    pthread_mutex_destroy(&debug_mutex);
    pthread_mutex_destroy(&python_wait_mutex);
    pthread_mutex_destroy(&python_mutex);
    return 0;
}

extern unsigned long __tick;

int WaitDebugData(unsigned long *tick)
{
    int res;
    if (PLC_shutdown) return 1;
    /* Wait signal from PLC thread */
    res = pthread_mutex_lock(&debug_wait_mutex);
    *tick = __debug_tick;
    return res;
}

/* Called by PLC thread when debug_publish finished
 * This is supposed to unlock debugger thread in WaitDebugData*/
void InitiateDebugTransfer()
{
    /* remember tick */
    __debug_tick = __tick;
    /* signal debugger thread it can read data */
    pthread_mutex_unlock(&debug_wait_mutex);
}

int suspendDebug(int disable)
{
    /* Prevent PLC to enter debug code */
    pthread_mutex_lock(&debug_mutex);
    /*__DEBUG is protected by this mutex */
    __DEBUG = !disable;
    if (disable)
    	pthread_mutex_unlock(&debug_mutex);
    return 0;
}

void resumeDebug(void)
{
    __DEBUG = 1;
    /* Let PLC enter debug code */
    pthread_mutex_unlock(&debug_mutex);
}

/* from plc_python.c */
int WaitPythonCommands(void)
{
    /* Wait signal from PLC thread */
    return pthread_mutex_lock(&python_wait_mutex);
}

/* Called by PLC thread on each new python command*/
void UnBlockPythonCommands(void)
{
    /* signal debugger thread it can read data */
    pthread_mutex_unlock(&python_wait_mutex);
}

int TryLockPython(void)
{
    return pthread_mutex_trylock(&python_mutex) == 0;
}

void UnLockPython(void)
{
    pthread_mutex_unlock(&python_mutex);
}

void LockPython(void)
{
    pthread_mutex_lock(&python_mutex);
}
