/**
 * Mac OSX specific code
 **/

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>
#include <pthread.h>
#include <locale.h>
#include <semaphore.h>
#include <dispatch/dispatch.h>

static dispatch_semaphore_t Run_PLC;

long AtomicCompareExchange(long *atomicvar, long compared, long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}

long long AtomicCompareExchange64(long long *atomicvar, long long compared,
                                  long long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}

void PLC_GetTime(IEC_TIME * CURRENT_TIME)
{
    struct timespec tmp;
    clock_gettime(CLOCK_REALTIME, &tmp);
    CURRENT_TIME->tv_sec = tmp.tv_sec;
    CURRENT_TIME->tv_nsec = tmp.tv_nsec;
}

dispatch_queue_t queue;
dispatch_source_t PLC_timer;

static inline void PLC_timer_cancel(void *arg)
{
    dispatch_release(PLC_timer);
    dispatch_release(queue);
    exit(0);
}

static inline void PLC_timer_notify(void *arg)
{
    PLC_GetTime(&__CURRENT_TIME);
    dispatch_semaphore_signal(Run_PLC);
}

void PLC_SetTimer(unsigned long long next, unsigned long long period)
{
    if (next == period && next == 0) {
        dispatch_suspend(PLC_timer);
    } else {
        dispatch_time_t start;
        start = dispatch_walltime(NULL, next);
        dispatch_source_set_timer(PLC_timer, start, period, 0);
        dispatch_resume(PLC_timer);
    }
}

void catch_signal(int sig)
{
    signal(SIGINT, catch_signal);
    printf("Got Signal %d\n", sig);
    dispatch_source_cancel(PLC_timer);
    exit(0);
}

static unsigned long __debug_tick;

pthread_t PLC_thread;
static pthread_mutex_t python_wait_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t python_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t debug_wait_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t debug_mutex = PTHREAD_MUTEX_INITIALIZER;

int PLC_shutdown = 0;

int ForceSaveRetainReq(void)
{
    return PLC_shutdown;
}

void PLC_thread_proc(void *arg)
{
    while (!PLC_shutdown) {
        dispatch_semaphore_wait(Run_PLC, DISPATCH_TIME_FOREVER);
        __run();
    }
    pthread_exit(0);
}

#define maxval(a,b) ((a>b)?a:b)
int startPLC(int argc, char **argv)
{
    setlocale(LC_NUMERIC, "C");

    PLC_shutdown = 0;

    Run_PLC = dispatch_semaphore_create(0);

    pthread_create(&PLC_thread, NULL, (void *)&PLC_thread_proc, NULL);

    pthread_mutex_init(&debug_wait_mutex, NULL);
    pthread_mutex_init(&debug_mutex, NULL);
    pthread_mutex_init(&python_wait_mutex, NULL);
    pthread_mutex_init(&python_mutex, NULL);

    pthread_mutex_lock(&debug_wait_mutex);
    pthread_mutex_lock(&python_wait_mutex);

    queue = dispatch_queue_create("timerQueue", 0);
    PLC_timer = dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER, 0, 0, queue);

    dispatch_set_context(PLC_timer, &PLC_timer);
    dispatch_source_set_event_handler_f(PLC_timer, PLC_timer_notify);
    dispatch_source_set_cancel_handler_f(PLC_timer, PLC_timer_cancel);

    if (__init(argc, argv) == 0) {
        PLC_SetTimer(common_ticktime__, common_ticktime__);

        /* install signal handler for manual break */
        signal(SIGINT, catch_signal);
    } else {
        return 1;
    }
    return 0;
}

int TryEnterDebugSection(void)
{
    if (pthread_mutex_trylock(&debug_mutex) == 0) {
        /* Only enter if debug active */
        if (__DEBUG) {
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
    dispatch_semaphore_signal(Run_PLC);
    PLC_SetTimer(0, 0);
    pthread_join(PLC_thread, NULL);
    dispatch_release(Run_PLC);
    Run_PLC = NULL;
    dispatch_source_cancel(PLC_timer);
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
    if (PLC_shutdown)
        return 1;
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
    /* signal python thread it can read data */
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

struct RT_to_nRT_signal_s {
    pthread_cond_t WakeCond;
    pthread_mutex_t WakeCondLock;
};

typedef struct RT_to_nRT_signal_s RT_to_nRT_signal_t;

#define _LogAndReturnNull(text) \
    {\
    	char mstr[256] = text " for ";\
        strncat(mstr, name, 255);\
        LogMessage(LOG_CRITICAL, mstr, strlen(mstr));\
        return NULL;\
    }

void *create_RT_to_nRT_signal(char *name)
{
    RT_to_nRT_signal_t *sig =
        (RT_to_nRT_signal_t *) malloc(sizeof(RT_to_nRT_signal_t));

    if (!sig)
        _LogAndReturnNull("Failed allocating memory for RT_to_nRT signal");

    pthread_cond_init(&sig->WakeCond, NULL);
    pthread_mutex_init(&sig->WakeCondLock, NULL);

    return (void *)sig;
}

void delete_RT_to_nRT_signal(void *handle)
{
    RT_to_nRT_signal_t *sig = (RT_to_nRT_signal_t *) handle;

    pthread_cond_destroy(&sig->WakeCond);
    pthread_mutex_destroy(&sig->WakeCondLock);

    free(sig);
}

int wait_RT_to_nRT_signal(void *handle)
{
    int ret;
    RT_to_nRT_signal_t *sig = (RT_to_nRT_signal_t *) handle;
    pthread_mutex_lock(&sig->WakeCondLock);
    ret = pthread_cond_wait(&sig->WakeCond, &sig->WakeCondLock);
    pthread_mutex_unlock(&sig->WakeCondLock);
    return ret;
}

int unblock_RT_to_nRT_signal(void *handle)
{
    RT_to_nRT_signal_t *sig = (RT_to_nRT_signal_t *) handle;
    return pthread_cond_signal(&sig->WakeCond);
}

void nRT_reschedule(void)
{
    sched_yield();
}
