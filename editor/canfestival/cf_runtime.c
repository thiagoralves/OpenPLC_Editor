
#include "canfestival.h"
#include "dcf.h"

/* CanFestival nodes generated OD headers*/
%(nodes_includes)s

#define BOARD_DECL(nodename, busname, baudrate)\
    s_BOARD nodename##Board = {busname, baudrate};

/* CAN channels declaration */
%(board_decls)s

/* Keep track of init level to cleanup correctly */
static int init_level=0;
/* Retrieve PLC cycle time */
extern unsigned long long common_ticktime__;

/* Per master node slavebootup callbacks. Checks that
 * every node have booted before calling Master_post_SlaveBootup */
%(slavebootups)s

/* One slave node post_sync callback.
 * Used to align PLC tick-time on CANopen SYNC
 */
%(post_sync)s

/* Triggers DCF transission
 */
%(pre_op)s

#define NODE_FORCE_SYNC(nodename) \
    /* Artificially force sync state to 1 so that it is not started */\
    nodename##_Data.CurrentCommunicationState.csSYNC = -1;\
    /* Force sync period to common_ticktime__ so that other node can read it*/\
    *nodename##_Data.COB_ID_Sync = 0x40000080;\
    *nodename##_Data.Sync_Cycle_Period = common_ticktime__ / 1000;

static void DeferedInitAlarm(CO_Data* d, UNS32 id){
    /* Node will start beeing active on the network after this */
    setState(d, Initialisation);
}

#define NODE_INIT(nodename, nodeid) \
    /* Defining the node Id */\
    setNodeId(&nodename##_Data, nodeid);\
    SetAlarm(&nodename##_Data,0,&DeferedInitAlarm,MS_TO_TIMEVAL(100),0);

#define NODE_MASTER_INIT(nodename, nodeid) \
    NODE_FORCE_SYNC(nodename) \
    NODE_INIT(nodename, nodeid)

#define NODE_SLAVE_INIT(nodename, nodeid) \
    NODE_INIT(nodename, nodeid)

static void InitNodes(CO_Data* d, UNS32 id)
{
    %(slavebootup_register)s
    %(post_sync_register)s
    %(pre_op_register)s
    %(nodes_init)s
}

#define NODE_STOP(nodename) \
    if(init_level-- > 0)\
    {\
        masterSendNMTstateChange(&nodename##_Data, 0, NMT_Reset_Node);\
        setState(&nodename##_Data, Stopped);\
    }

static void Exit(CO_Data* d, UNS32 id)
{
    %(nodes_stop)s
}

#define NODE_CLOSE(nodename) \
    if(init_level_c-- > 0)\
    {\
      canClose(&nodename##_Data);\
    }

void __cleanup_%(locstr)s(void)
{
    // Stop timer thread
    if(init_level-- > 0){
    int init_level_c = init_level;
        StopTimerLoop(&Exit);
        %(nodes_close)s
    }

    TimerCleanup();
}

#ifndef stderr
#define fprintf(...)
#define fflush(...)
#endif

#define NODE_OPEN(nodename)\
    if(!canOpen(&nodename##Board,&nodename##_Data)){\
        fprintf(stderr,"Cannot open CAN intefrace %%s at speed %%s\n for CANopen node \"" #nodename "\"",nodename##Board.busname, nodename##Board.baudrate);\
        fflush(stderr);\
        return -1;\
    }\
    init_level++;

/***************************  INIT  *****************************************/
int __init_%(locstr)s(int argc,char **argv)
{
#ifndef NOT_USE_DYNAMIC_LOADING
    if( !LoadCanDriver("%(candriver)s") ){
        fprintf(stderr, "Cannot load CAN interface library for CanFestival (%(candriver)s)\n");\
        fflush(stderr);\
        return -1;\
    }
#endif

    TimerInit();

    %(nodes_open)s

    // Start timer thread
    StartTimerLoop(&InitNodes);
    init_level++;
    return 0;
}

#define NODE_SEND_SYNC(nodename)\
    if(getState(&nodename##_Data)==Operational){\
        sendSYNCMessage(&nodename##_Data);\
    }

void __retrieve_%(locstr)s(void)
{
    /* Locks the stack, so that no changes occurs while PLC access variables
     * TODO : implement buffers to avoid such a big lock
     *  */
    EnterMutex();
    /* Send Sync */
    %(nodes_send_sync)s
}

#define NODE_PROCEED_SYNC(nodename)\
    proceedSYNC(&nodename##_Data);

void __publish_%(locstr)s(void)
{
    /* Process sync event */
    %(nodes_proceed_sync)s
    LeaveMutex();
}

