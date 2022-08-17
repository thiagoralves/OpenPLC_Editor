/**
 * Xenomai Linux specific code
 **/

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/mman.h>
#include <sys/fcntl.h>

#include <alchemy/task.h>
#include <alchemy/timer.h>
#include <alchemy/sem.h>
#include <alchemy/pipe.h>

unsigned int PLC_state = 0;
#define PLC_STATE_TASK_CREATED                 1
#define PLC_STATE_DEBUG_PIPE_CREATED           2
#define PLC_STATE_PYTHON_PIPE_CREATED          8
#define PLC_STATE_WAITDEBUG_PIPE_CREATED       16
#define PLC_STATE_WAITPYTHON_PIPE_CREATED      32

#define PIPE_SIZE                    1

// rt-pipes commands

#define PYTHON_PENDING_COMMAND 1
#define PYTHON_FINISH 2

#define DEBUG_FINISH 2

#define DEBUG_PENDING_DATA 1
#define DEBUG_UNLOCK 1

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
    RTIME current_time = rt_timer_read();
    CURRENT_TIME->tv_sec = current_time / 1000000000;
    CURRENT_TIME->tv_nsec = current_time % 1000000000;
}

RT_TASK PLC_task;
void *WaitDebug_handle;
void *WaitPython_handle;
void *Debug_handle;
void *Python_handle;
void *svghmi_handle;

struct RT_to_nRT_signal_s {
    int used;
    RT_PIPE pipe;
    int pipe_fd;
    char *name;
};
typedef struct RT_to_nRT_signal_s RT_to_nRT_signal_t;

#define max_RT_to_nRT_signals 16

static RT_to_nRT_signal_t RT_to_nRT_signal_pool[max_RT_to_nRT_signals];

int recv_RT_to_nRT_signal(void* handle, char* payload){
    RT_to_nRT_signal_t *sig = (RT_to_nRT_signal_t*)handle;
    if(!sig->used) return -EINVAL;
    return read(sig->pipe_fd, payload, 1);
}

int send_RT_to_nRT_signal(void* handle, char payload){
    RT_to_nRT_signal_t *sig = (RT_to_nRT_signal_t*)handle;
    if(!sig->used) return -EINVAL;
    return rt_pipe_write(&sig->pipe, &payload, 1, P_NORMAL);
}


int PLC_shutdown = 0;

void PLC_SetTimer(unsigned long long next, unsigned long long period)
{
  RTIME current_time = rt_timer_read();
  rt_task_set_periodic(&PLC_task, current_time + next, rt_timer_ns2ticks(period));
}

void PLC_task_proc(void *arg)
{
    PLC_SetTimer(common_ticktime__, common_ticktime__);

    while (!PLC_shutdown) {
        PLC_GetTime(&__CURRENT_TIME);
        __run();
        if (PLC_shutdown) break;
        rt_task_wait_period(NULL);
    }
    /* since xenomai 3 it is not enough to close()
       file descriptor to unblock read()... */
    {
        /* explicitely finish python thread */
        char msg = PYTHON_FINISH;
        send_RT_to_nRT_signal(WaitPython_handle, msg);
    }
    {
        /* explicitely finish debug thread */
        char msg = DEBUG_FINISH;
        send_RT_to_nRT_signal(WaitDebug_handle, msg);
    }
}

static unsigned long __debug_tick;

#define _Log(text, err) \
    {\
        char mstr[256];\
        snprintf(mstr, 255, text " for %s (%d)", name, err);\
        LogMessage(LOG_CRITICAL, mstr, strlen(mstr));\
    }

void *create_RT_to_nRT_signal(char* name){
    int new_index = -1;
    int ret;
    RT_to_nRT_signal_t *sig;
    char pipe_dev[64];

    /* find a free slot */
    for(int i=0; i < max_RT_to_nRT_signals; i++){
        sig = &RT_to_nRT_signal_pool[i];
        if(!sig->used){
            new_index = i;
            break;
        }
    }

    /* fail if none found */
    if(new_index == -1) {
    	_Log("Maximum count of RT-PIPE reached while creating pipe", max_RT_to_nRT_signals);
        return NULL;
    }

    /* create rt pipe */
    if(ret = rt_pipe_create(&sig->pipe, name, new_index, PIPE_SIZE) < 0){
    	_Log("Failed opening real-time end of RT-PIPE", ret);
        return NULL;
    }

    /* open pipe's userland */
    snprintf(pipe_dev, 63, "/dev/rtp%d", new_index);
    if((sig->pipe_fd = open(pipe_dev, O_RDWR)) == -1){
        rt_pipe_delete(&sig->pipe);
    	_Log("Failed opening non-real-time end of RT-PIPE", errno);
        return NULL;
    }

    sig->used = 1;
    sig->name = name;

    return sig;
}

void delete_RT_to_nRT_signal(void* handle){
    int ret;
    RT_to_nRT_signal_t *sig = (RT_to_nRT_signal_t*)handle;
    char *name = sig->name;

    if(!sig->used) return;

    if(ret = rt_pipe_delete(&sig->pipe) != 0){
    	_Log("Failed closing real-time end of RT-PIPE", ret);
    }

    if(close(sig->pipe_fd) != 0){
    	_Log("Failed closing non-real-time end of RT-PIPE", errno);
    }

    sig->used = 0;
}

int wait_RT_to_nRT_signal(void* handle){
    char cmd;
    int ret = recv_RT_to_nRT_signal(handle, &cmd);
    return (ret == 1) ? 0 : ((ret == 0) ? ENODATA : -ret);
}

int unblock_RT_to_nRT_signal(void* handle){
    int ret = send_RT_to_nRT_signal(handle, 0);
    return (ret == 1) ? 0 : ((ret == 0) ? EINVAL : -ret);
}

void nRT_reschedule(void){
    sched_yield();
}

void PLC_cleanup_all(void)
{
    if (PLC_state & PLC_STATE_TASK_CREATED) {
        rt_task_delete(&PLC_task);
        PLC_state &= ~PLC_STATE_TASK_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITDEBUG_PIPE_CREATED) {
        delete_RT_to_nRT_signal(WaitDebug_handle);
        PLC_state &= ~PLC_STATE_WAITDEBUG_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITPYTHON_PIPE_CREATED) {
        delete_RT_to_nRT_signal(WaitPython_handle);
        PLC_state &= ~PLC_STATE_WAITPYTHON_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_DEBUG_PIPE_CREATED) {
        delete_RT_to_nRT_signal(Debug_handle);
        PLC_state &= ~PLC_STATE_DEBUG_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_PYTHON_PIPE_CREATED) {
        delete_RT_to_nRT_signal(Python_handle);
        PLC_state &= ~PLC_STATE_PYTHON_PIPE_CREATED;
    }
}

int stopPLC()
{
    /* Stop the PLC */
    PLC_shutdown = 1;

    /* Wait until PLC task stops */
    rt_task_join(&PLC_task);

    PLC_cleanup_all();
    __cleanup();
    __debug_tick = -1;
    return 0;
}

//
void catch_signal(int sig)
{
    stopPLC();
//  signal(SIGTERM, catch_signal);
    signal(SIGINT, catch_signal);
    printf("Got Signal %d\n",sig);
    exit(0);
}

#define _startPLCLog(text) \
    {\
    	char mstr[] = text;\
        LogMessage(LOG_CRITICAL, mstr, sizeof(mstr));\
        goto error;\
    }

#define FO "Failed opening "

#define max_val(a,b) ((a>b)?a:b)
int startPLC(int argc,char **argv)
{
    signal(SIGINT, catch_signal);

    /* no memory swapping for that process */
    mlockall(MCL_CURRENT | MCL_FUTURE);

    /* memory initialization */
    PLC_shutdown = 0;
    bzero(RT_to_nRT_signal_pool, sizeof(RT_to_nRT_signal_pool));

    /*** RT Pipes ***/
    /* create Debug_pipe */
    if(!(Debug_handle = create_RT_to_nRT_signal("Debug_pipe"))) goto error;
    PLC_state |= PLC_STATE_DEBUG_PIPE_CREATED;

    /* create Python_pipe */
    if(!(Python_handle = create_RT_to_nRT_signal("Python_pipe"))) goto error;
    PLC_state |= PLC_STATE_PYTHON_PIPE_CREATED;

    /* create WaitDebug_pipe */
    if(!(WaitDebug_handle = create_RT_to_nRT_signal("WaitDebug_pipe"))) goto error;
    PLC_state |= PLC_STATE_WAITDEBUG_PIPE_CREATED;

    /* create WaitPython_pipe */
    if(!(WaitPython_handle = create_RT_to_nRT_signal("WaitPython_pipe"))) goto error;
    PLC_state |= PLC_STATE_WAITPYTHON_PIPE_CREATED;

    /*** create PLC task ***/
    if(rt_task_create(&PLC_task, "PLC_task", 0, 50, T_JOINABLE))
        _startPLCLog("Failed creating PLC task");
    PLC_state |= PLC_STATE_TASK_CREATED;

    if(__init(argc,argv)) goto error;

    /* start PLC task */
    if(rt_task_start(&PLC_task, &PLC_task_proc, NULL))
        _startPLCLog("Failed starting PLC task");

    return 0;

error:

    PLC_cleanup_all();
    return 1;
}

#define DEBUG_FREE 0
#define DEBUG_BUSY 1
static long debug_state = DEBUG_FREE;

int TryEnterDebugSection(void)
{
    if(AtomicCompareExchange(
        &debug_state,
        DEBUG_FREE,
        DEBUG_BUSY) == DEBUG_FREE){
        if(__DEBUG){
            return 1;
        }
        AtomicCompareExchange( &debug_state, DEBUG_BUSY, DEBUG_FREE);
    }
    return 0;
}

void LeaveDebugSection(void)
{
    if(AtomicCompareExchange( &debug_state,
        DEBUG_BUSY, DEBUG_FREE) == DEBUG_BUSY){
        char msg = DEBUG_UNLOCK;
        /* signal to NRT for wakeup */
        send_RT_to_nRT_signal(Debug_handle, msg);
    }
}

extern unsigned long __tick;

int WaitDebugData(unsigned long *tick)
{
    char cmd;
    int res;
    if (PLC_shutdown) return -1;
    /* Wait signal from PLC thread */
    res = recv_RT_to_nRT_signal(WaitDebug_handle, &cmd);
    if (res == 1 && cmd == DEBUG_PENDING_DATA){
        *tick = __debug_tick;
        return 0;
    }
    return -1;
}

/* Called by PLC thread when debug_publish finished
 * This is supposed to unlock debugger thread in WaitDebugData*/
void InitiateDebugTransfer()
{
    char msg = DEBUG_PENDING_DATA;
    /* remember tick */
    __debug_tick = __tick;
    /* signal debugger thread it can read data */
    send_RT_to_nRT_signal(WaitDebug_handle, msg);
}

int suspendDebug(int disable)
{
    char cmd = DEBUG_UNLOCK;
    if (PLC_shutdown) return -1;
    while(AtomicCompareExchange(
            &debug_state,
            DEBUG_FREE,
            DEBUG_BUSY) != DEBUG_FREE &&
            cmd == DEBUG_UNLOCK){
       if(recv_RT_to_nRT_signal(Debug_handle, &cmd) != 1){
           return -1;
       }
    }
    __DEBUG = !disable;
    if (disable)
        AtomicCompareExchange( &debug_state, DEBUG_BUSY, DEBUG_FREE);
    return 0;
}

void resumeDebug(void)
{
    __DEBUG = 1;
    AtomicCompareExchange( &debug_state, DEBUG_BUSY, DEBUG_FREE);
}

#define PYTHON_FREE 0
#define PYTHON_BUSY 1
static long python_state = PYTHON_FREE;

int WaitPythonCommands(void)
{
    char cmd;
    if (PLC_shutdown) return -1;
    /* Wait signal from PLC thread */
    if(recv_RT_to_nRT_signal(WaitPython_handle, &cmd) == 1 && cmd==PYTHON_PENDING_COMMAND){
        return 0;
    }
    return -1;
}

/* Called by PLC thread on each new python command*/
void UnBlockPythonCommands(void)
{
    char msg = PYTHON_PENDING_COMMAND;
    send_RT_to_nRT_signal(WaitPython_handle, msg);
}

int TryLockPython(void)
{
    return AtomicCompareExchange(
        &python_state,
        PYTHON_FREE,
        PYTHON_BUSY) == PYTHON_FREE;
}

#define UNLOCK_PYTHON 1
void LockPython(void)
{
    char cmd = UNLOCK_PYTHON;
    if (PLC_shutdown) return;
    while(AtomicCompareExchange(
            &python_state,
            PYTHON_FREE,
            PYTHON_BUSY) != PYTHON_FREE &&
            cmd == UNLOCK_PYTHON){
       recv_RT_to_nRT_signal(Python_handle, &cmd);
    }
}

void UnLockPython(void)
{
    if(AtomicCompareExchange(
            &python_state,
            PYTHON_BUSY,
            PYTHON_FREE) == PYTHON_BUSY){
        if(rt_task_self()){/*is that the real time task ?*/
           char cmd = UNLOCK_PYTHON;
           send_RT_to_nRT_signal(Python_handle, cmd);
        }/* otherwise, no signaling from non real time */
    }    /* as plc does not wait for lock. */
}

#ifndef HAVE_RETAIN
int CheckRetainBuffer(void)
{
	return 1;
}

void ValidateRetainBuffer(void)
{
}

void InValidateRetainBuffer(void)
{
}

void Retain(unsigned int offset, unsigned int count, void *p)
{
}

void Remind(unsigned int offset, unsigned int count, void *p)
{
}

void CleanupRetain(void)
{
}

void InitRetain(void)
{
}
#endif // !HAVE_RETAIN
