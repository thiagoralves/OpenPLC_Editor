/**
 * Xenomai Linux specific code
 **/

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/fcntl.h>

#include <alchemy/task.h>
#include <alchemy/timer.h>
#include <alchemy/sem.h>
#include <alchemy/pipe.h>

unsigned int PLC_state = 0;
#define PLC_STATE_TASK_CREATED                 1
#define PLC_STATE_DEBUG_FILE_OPENED            2 
#define PLC_STATE_DEBUG_PIPE_CREATED           4 
#define PLC_STATE_PYTHON_FILE_OPENED           8 
#define PLC_STATE_PYTHON_PIPE_CREATED          16   
#define PLC_STATE_WAITDEBUG_FILE_OPENED        32   
#define PLC_STATE_WAITDEBUG_PIPE_CREATED       64
#define PLC_STATE_WAITPYTHON_FILE_OPENED       128
#define PLC_STATE_WAITPYTHON_PIPE_CREATED      256

#define WAITDEBUG_PIPE_DEVICE        "/dev/rtp0"
#define WAITDEBUG_PIPE_MINOR         0
#define DEBUG_PIPE_DEVICE            "/dev/rtp1"
#define DEBUG_PIPE_MINOR             1
#define WAITPYTHON_PIPE_DEVICE       "/dev/rtp2"
#define WAITPYTHON_PIPE_MINOR        2
#define PYTHON_PIPE_DEVICE           "/dev/rtp3"
#define PYTHON_PIPE_MINOR            3
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
RT_PIPE WaitDebug_pipe;
RT_PIPE WaitPython_pipe;
RT_PIPE Debug_pipe;
RT_PIPE Python_pipe;
int WaitDebug_pipe_fd;
int WaitPython_pipe_fd;
int Debug_pipe_fd;
int Python_pipe_fd;

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
        rt_pipe_write(&WaitPython_pipe, &msg, sizeof(msg), P_NORMAL);
    }
    {
        /* explicitely finish debug thread */
        char msg = DEBUG_FINISH;
        rt_pipe_write(&WaitDebug_pipe, &msg, sizeof(msg), P_NORMAL);
    }
}

static unsigned long __debug_tick;

void PLC_cleanup_all(void)
{
    if (PLC_state & PLC_STATE_TASK_CREATED) {
        rt_task_delete(&PLC_task);
        PLC_state &= ~PLC_STATE_TASK_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITDEBUG_PIPE_CREATED) {
        rt_pipe_delete(&WaitDebug_pipe);
        PLC_state &= ~PLC_STATE_WAITDEBUG_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITDEBUG_FILE_OPENED) {
        close(WaitDebug_pipe_fd);
        PLC_state &= ~PLC_STATE_WAITDEBUG_FILE_OPENED;
    }

    if (PLC_state & PLC_STATE_WAITPYTHON_PIPE_CREATED) {
        rt_pipe_delete(&WaitPython_pipe);
        PLC_state &= ~PLC_STATE_WAITPYTHON_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITPYTHON_FILE_OPENED) {
        close(WaitPython_pipe_fd);
        PLC_state &= ~PLC_STATE_WAITPYTHON_FILE_OPENED;
    }

    if (PLC_state & PLC_STATE_DEBUG_PIPE_CREATED) {
        rt_pipe_delete(&Debug_pipe);
        PLC_state &= ~PLC_STATE_DEBUG_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_DEBUG_FILE_OPENED) {
        close(Debug_pipe_fd);
        PLC_state &= ~PLC_STATE_DEBUG_FILE_OPENED;
    }

    if (PLC_state & PLC_STATE_PYTHON_PIPE_CREATED) {
        rt_pipe_delete(&Python_pipe);
        PLC_state &= ~PLC_STATE_PYTHON_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_PYTHON_FILE_OPENED) {
        close(Python_pipe_fd);
        PLC_state &= ~PLC_STATE_PYTHON_FILE_OPENED;
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

    PLC_shutdown = 0;

    /*** RT Pipes creation and opening ***/
    /* create Debug_pipe */
    if(rt_pipe_create(&Debug_pipe, "Debug_pipe", DEBUG_PIPE_MINOR, PIPE_SIZE) < 0) 
        _startPLCLog(FO "Debug_pipe real-time end");
    PLC_state |= PLC_STATE_DEBUG_PIPE_CREATED;

    /* open Debug_pipe*/
    if((Debug_pipe_fd = open(DEBUG_PIPE_DEVICE, O_RDWR)) == -1)
        _startPLCLog(FO DEBUG_PIPE_DEVICE);
    PLC_state |= PLC_STATE_DEBUG_FILE_OPENED;

    /* create Python_pipe */
    if(rt_pipe_create(&Python_pipe, "Python_pipe", PYTHON_PIPE_MINOR, PIPE_SIZE) < 0) 
        _startPLCLog(FO "Python_pipe real-time end");
    PLC_state |= PLC_STATE_PYTHON_PIPE_CREATED;

    /* open Python_pipe*/
    if((Python_pipe_fd = open(PYTHON_PIPE_DEVICE, O_RDWR)) == -1)
        _startPLCLog(FO PYTHON_PIPE_DEVICE);
    PLC_state |= PLC_STATE_PYTHON_FILE_OPENED;

    /* create WaitDebug_pipe */
    if(rt_pipe_create(&WaitDebug_pipe, "WaitDebug_pipe", WAITDEBUG_PIPE_MINOR, PIPE_SIZE) < 0)
        _startPLCLog(FO "WaitDebug_pipe real-time end");
    PLC_state |= PLC_STATE_WAITDEBUG_PIPE_CREATED;

    /* open WaitDebug_pipe*/
    if((WaitDebug_pipe_fd = open(WAITDEBUG_PIPE_DEVICE, O_RDWR)) == -1)
        _startPLCLog(FO WAITDEBUG_PIPE_DEVICE);
    PLC_state |= PLC_STATE_WAITDEBUG_FILE_OPENED;

    /* create WaitPython_pipe */
    if(rt_pipe_create(&WaitPython_pipe, "WaitPython_pipe", WAITPYTHON_PIPE_MINOR, PIPE_SIZE) < 0)
        _startPLCLog(FO "WaitPython_pipe real-time end");
    PLC_state |= PLC_STATE_WAITPYTHON_PIPE_CREATED;

    /* open WaitPython_pipe*/
    if((WaitPython_pipe_fd = open(WAITPYTHON_PIPE_DEVICE, O_RDWR)) == -1)
        _startPLCLog(FO WAITPYTHON_PIPE_DEVICE);
    PLC_state |= PLC_STATE_WAITPYTHON_FILE_OPENED;

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
        rt_pipe_write(&Debug_pipe, &msg, sizeof(msg), P_NORMAL);
    }
}

extern unsigned long __tick;

int WaitDebugData(unsigned long *tick)
{
    char cmd;
    int res;
    if (PLC_shutdown) return -1;
    /* Wait signal from PLC thread */
    res = read(WaitDebug_pipe_fd, &cmd, sizeof(cmd));
    if (res == sizeof(cmd) && cmd == DEBUG_PENDING_DATA){
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
    rt_pipe_write(&WaitDebug_pipe, &msg, sizeof(msg), P_NORMAL);
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
       if(read(Debug_pipe_fd, &cmd, sizeof(cmd)) != sizeof(cmd)){
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
    if(read(WaitPython_pipe_fd, &cmd, sizeof(cmd))==sizeof(cmd) && cmd==PYTHON_PENDING_COMMAND){
        return 0;
    }
    return -1;
}

/* Called by PLC thread on each new python command*/
void UnBlockPythonCommands(void)
{
    char msg = PYTHON_PENDING_COMMAND;
    rt_pipe_write(&WaitPython_pipe, &msg, sizeof(msg), P_NORMAL);
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
       read(Python_pipe_fd, &cmd, sizeof(cmd));
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
           rt_pipe_write(&Python_pipe, &cmd, sizeof(cmd), P_NORMAL);
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
