#include <pthread.h>
#include <errno.h>
#include "iec_types_all.h"
#include "POUS.h"
#include "config.h"
#include "beremiz.h"

#define DEFAULT_REFRESH_PERIOD_MS 100
#define HMI_BUFFER_SIZE %(buffer_size)d
#define HMI_ITEM_COUNT %(item_count)d
#define HMI_HASH_SIZE 8
#define MAX_CONNECTIONS %(max_connections)d
#define MAX_CON_INDEX MAX_CONNECTIONS - 1

static uint8_t hmi_hash[HMI_HASH_SIZE] = {%(hmi_hash_ints)s};

/* PLC reads from that buffer */
static char rbuf[HMI_BUFFER_SIZE];

/* PLC writes to that buffer */
static char wbuf[HMI_BUFFER_SIZE];

/* worst biggest send buffer. FIXME : use dynamic alloc ? */
static char sbuf[HMI_HASH_SIZE +  HMI_BUFFER_SIZE + (HMI_ITEM_COUNT * sizeof(uint32_t))];
static unsigned int sbufidx;

%(extern_variables_declarations)s

#define ticktime_ns %(PLC_ticktime)d
static uint16_t ticktime_ms = (ticktime_ns>1000000)?
                     ticktime_ns/1000000:
                     1;

typedef enum {
    buf_free = 0,
    buf_new,
    buf_set,
    buf_tosend
} buf_state_t;

static int global_write_dirty = 0;
static long hmitree_rlock = 0;
static long hmitree_wlock = 0;

typedef struct hmi_tree_item_s hmi_tree_item_t;
struct hmi_tree_item_s{
    void *ptr;
    __IEC_types_enum type;
    uint32_t buf_index;

    /* retrieve/read/recv */
    buf_state_t rstate;

    /* publish/write/send */
    buf_state_t wstate[MAX_CONNECTIONS];

    /* zero means not subscribed */
    uint16_t refresh_period_ms[MAX_CONNECTIONS];
    uint16_t age_ms[MAX_CONNECTIONS];

    /* dual linked list for subscriptions */
    hmi_tree_item_t *subscriptions_next;
    hmi_tree_item_t *subscriptions_prev;

    /* single linked list for changes from HMI */
    hmi_tree_item_t *incoming_prev;

};

#define HMITREE_ITEM_INITIALIZER(cpath,type,buf_index) {        \
    &(cpath),                             /*ptr*/               \
    type,                                 /*type*/              \
    buf_index,                            /*buf_index*/         \
    buf_free,                             /*rstate*/            \
    {[0 ... MAX_CON_INDEX] = buf_free},   /*wstate*/            \
    {[0 ... MAX_CON_INDEX] = 0},          /*refresh_period_ms*/ \
    {[0 ... MAX_CON_INDEX] = 0},          /*age_ms*/            \
    NULL,                                 /*subscriptions_next*/\
    NULL,                                 /*subscriptions_prev*/\
    NULL}                                 /*incoming_next*/


/* entry for dual linked list for HMI subscriptions */
/* points to the end of the list */
static hmi_tree_item_t  *subscriptions_tail = NULL;

/* entry for single linked list for changes from HMI */
/* points to the end of the list */
static hmi_tree_item_t *incoming_tail = NULL;

static hmi_tree_item_t hmi_tree_items[] = {
%(variable_decl_array)s
};

#define __Unpack_desc_type hmi_tree_item_t

%(var_access_code)s

static int write_iterator(hmi_tree_item_t *dsc)
{
    uint32_t session_index = 0;
    int value_changed = 0;
    void *dest_p = NULL;
    void *value_p = NULL;
    size_t sz = 0;
    while(session_index < MAX_CONNECTIONS) {
        if(dsc->wstate[session_index] == buf_set){
            /* if being subscribed */
            if(dsc->refresh_period_ms[session_index]){
                if(dsc->age_ms[session_index] + ticktime_ms < dsc->refresh_period_ms[session_index]){
                    dsc->age_ms[session_index] += ticktime_ms;
                }else{
                    dsc->wstate[session_index] = buf_tosend;
                    global_write_dirty = 1;
                }
            }
        }

        /* variable is sample only if just subscribed
           or already subscribed and having value change */
        int do_sample = 0;
        int just_subscribed = dsc->wstate[session_index] == buf_new;
        if(!just_subscribed){
            int already_subscribed = dsc->refresh_period_ms[session_index] > 0;
            if(already_subscribed){
                if(!value_changed){
                    if(!value_p){
                        UnpackVar(dsc, &value_p, NULL, &sz);
                        if(__Is_a_string(dsc)){
                            sz = ((STRING*)value_p)->len + 1;
                        }
                        dest_p = &wbuf[dsc->buf_index];
                    }
                    value_changed = memcmp(dest_p, value_p, sz) != 0;
                    do_sample = value_changed;
                }else{
                    do_sample = 1;
                }
            }
        } else {
            do_sample = 1;
        }


        if(do_sample){
            if(dsc->wstate[session_index] != buf_set && dsc->wstate[session_index] != buf_tosend) {
                if(dsc->wstate[session_index] == buf_new \
                   || ticktime_ms > dsc->refresh_period_ms[session_index]){
                    dsc->wstate[session_index] = buf_tosend;
                    global_write_dirty = 1;
                } else {
                    dsc->wstate[session_index] = buf_set;
                }
                dsc->age_ms[session_index] = 0;
            }
        }

        session_index++;
    }
    /* copy value if changed (and subscribed) */
    if(value_changed)
        memcpy(dest_p, value_p, sz);
    return 0;
}

static int send_iterator(uint32_t index, hmi_tree_item_t *dsc, uint32_t session_index)
{
    if(dsc->wstate[session_index] == buf_tosend)
    {
        uint32_t sz = __get_type_enum_size(dsc->type);
        if(sbufidx + sizeof(uint32_t) + sz <=  sizeof(sbuf))
        {
            void *src_p = &wbuf[dsc->buf_index];
            void *dst_p = &sbuf[sbufidx];
            if(__Is_a_string(dsc)){
                sz = ((STRING*)src_p)->len + 1;
            }
            /* TODO : force into little endian */
            memcpy(dst_p, &index, sizeof(uint32_t));
            memcpy(dst_p + sizeof(uint32_t), src_p, sz);
            dsc->wstate[session_index] = buf_free;
            sbufidx += sizeof(uint32_t) /* index */ + sz;
        }
        else
        {
            printf("BUG!!! %%d + %%ld + %%d >  %%ld \n", sbufidx, sizeof(uint32_t), sz,  sizeof(sbuf));
            return EOVERFLOW;
        }
    }

    return 0;
}

static int read_iterator(hmi_tree_item_t *dsc)
{
    if(dsc->rstate == buf_set)
    {
        void *src_p = &rbuf[dsc->buf_index];
        void *value_p = NULL;
        size_t sz = 0;
        UnpackVar(dsc, &value_p, NULL, &sz);
        memcpy(value_p, src_p, sz);
        dsc->rstate = buf_free;
    }
    return 0;
}

void update_refresh_period(hmi_tree_item_t *dsc, uint32_t session_index, uint16_t refresh_period_ms)
{
    uint32_t other_session_index = 0;
    int previously_subscribed = 0;
    int session_only_subscriber = 0;
    int session_already_subscriber = 0;
    int needs_subscription_for_session = (refresh_period_ms != 0);

    while(other_session_index < session_index) {
        previously_subscribed |= (dsc->refresh_period_ms[other_session_index++] != 0);
    }
    session_already_subscriber = (dsc->refresh_period_ms[other_session_index++] != 0);
    while(other_session_index < MAX_CONNECTIONS) {
        previously_subscribed |= (dsc->refresh_period_ms[other_session_index++] != 0);
    }
    session_only_subscriber = session_already_subscriber && !previously_subscribed;
    previously_subscribed |= session_already_subscriber;

    if(needs_subscription_for_session) {
        if(!session_already_subscriber)
        {
            dsc->wstate[session_index] = buf_new;
        }
        /* item is appended to list only when no session was previously subscribed */
        if(!previously_subscribed){
            /* append subsciption to list */
            if(subscriptions_tail != NULL){ 
                /* if list wasn't empty, link with previous tail*/
                subscriptions_tail->subscriptions_next = dsc;
            }
            dsc->subscriptions_prev = subscriptions_tail;
            subscriptions_tail = dsc;
            dsc->subscriptions_next = NULL;
        }
    } else {
        dsc->wstate[session_index] = buf_free;
        /* item is removed from list only when session was the only one remaining */
        if (session_only_subscriber) {
            if(dsc->subscriptions_next == NULL){ /* remove tail  */
                /* re-link tail to previous */
                subscriptions_tail = dsc->subscriptions_prev;
                if(subscriptions_tail != NULL){
                    subscriptions_tail->subscriptions_next = NULL;
                }
            } else if(dsc->subscriptions_prev == NULL){ /* remove head  */
                dsc->subscriptions_next->subscriptions_prev = NULL;
            } else { /* remove entry in between other entries */
                /* re-link previous and next node */
                dsc->subscriptions_next->subscriptions_prev = dsc->subscriptions_prev;
                dsc->subscriptions_prev->subscriptions_next = dsc->subscriptions_next;
            }
            /* unnecessary
            dsc->subscriptions_next = NULL;
            dsc->subscriptions_prev = NULL;
            */
        }
    }
    dsc->refresh_period_ms[session_index] = refresh_period_ms;
}

static void *svghmi_handle;

void SVGHMI_SuspendFromPythonThread(void)
{
    wait_RT_to_nRT_signal(svghmi_handle);
}

void SVGHMI_WakeupFromRTThread(void)
{
    unblock_RT_to_nRT_signal(svghmi_handle);
}

int svghmi_continue_collect;

int __init_svghmi()
{
    memset(rbuf,0,sizeof(rbuf));
    memset(wbuf,0,sizeof(wbuf));

    svghmi_continue_collect = 1;

    /* create svghmi_pipe */
    svghmi_handle = create_RT_to_nRT_signal("SVGHMI_pipe");

    if(!svghmi_handle)
        return 1;

    return 0;
}

void __cleanup_svghmi()
{
    svghmi_continue_collect = 0;
    SVGHMI_WakeupFromRTThread();
    delete_RT_to_nRT_signal(svghmi_handle);
}

void __retrieve_svghmi()
{
    if(AtomicCompareExchange(&hmitree_rlock, 0, 1) == 0) {
        hmi_tree_item_t *dsc = incoming_tail;
        /* iterate through read list (changes from HMI) */
        while(dsc){
            hmi_tree_item_t *_dsc = dsc->incoming_prev;
            read_iterator(dsc);
            /* unnecessary
            dsc->incoming_prev = NULL;
            */
            dsc = _dsc;
        }
        /* flush read list */
        incoming_tail = NULL;
        AtomicCompareExchange(&hmitree_rlock, 1, 0);
    }
}

void __publish_svghmi()
{
    global_write_dirty = 0;

    if(AtomicCompareExchange(&hmitree_wlock, 0, 1) == 0) {
        hmi_tree_item_t *dsc = subscriptions_tail;
        while(dsc){
            write_iterator(dsc);
            dsc = dsc->subscriptions_prev;
        }
        AtomicCompareExchange(&hmitree_wlock, 1, 0);
    }

    if(global_write_dirty) {
        SVGHMI_WakeupFromRTThread();
    }
}

/* PYTHON CALLS */
int svghmi_wait(void){

    SVGHMI_SuspendFromPythonThread();
}

int svghmi_send_collect(uint32_t session_index, uint32_t *size, char **ptr){


    if(svghmi_continue_collect) {
        int res;
        sbufidx = HMI_HASH_SIZE;

        while(AtomicCompareExchange(&hmitree_wlock, 0, 1)){
            nRT_reschedule();
        }

        hmi_tree_item_t *dsc = subscriptions_tail;
        while(dsc){
            uint32_t index = dsc - hmi_tree_items;
            res = send_iterator(index, dsc, session_index);
            if(res != 0){
                break;
            }
            dsc = dsc->subscriptions_prev;
        }
        if(res == 0)
        {
            if(sbufidx > HMI_HASH_SIZE){
                memcpy(&sbuf[0], &hmi_hash[0], HMI_HASH_SIZE);
                *ptr = &sbuf[0];
                *size = sbufidx;
                AtomicCompareExchange(&hmitree_wlock, 1, 0);
                return 0;
            }
            AtomicCompareExchange(&hmitree_wlock, 1, 0);
            return ENODATA;
        }
        AtomicCompareExchange(&hmitree_wlock, 1, 0);
        return res;
    }
    else
    {
        return EINTR;
    }
}

typedef enum {
    unset = -1,
    setval = 0,
    reset = 1,
    subscribe = 2
} cmd_from_JS;

int svghmi_reset(uint32_t session_index){
    hmi_tree_item_t *dsc = subscriptions_tail;
    while(AtomicCompareExchange(&hmitree_wlock, 0, 1)){
        nRT_reschedule();
    }
    while(dsc){
        hmi_tree_item_t *_dsc = dsc->subscriptions_prev;
        update_refresh_period(dsc, session_index, 0);
        dsc = _dsc;
    }
    AtomicCompareExchange(&hmitree_wlock, 1, 0);
    return 1;
}

// Returns :
//   0 is OK, <0 is error, 1 is heartbeat
int svghmi_recv_dispatch(uint32_t session_index, uint32_t size, const uint8_t *ptr){
    const uint8_t* cursor = ptr + HMI_HASH_SIZE;
    const uint8_t* end = ptr + size;

    int was_hearbeat = 0;

    /* match hmitree fingerprint */
    if(size <= HMI_HASH_SIZE || memcmp(ptr, hmi_hash, HMI_HASH_SIZE) != 0)
    {
        printf("svghmi_recv_dispatch MISMATCH !!\n");
        return -EINVAL;
    }

    int ret;
    int got_wlock = 0;
    int got_rlock = 0;
    cmd_from_JS cmd_old = unset;
    cmd_from_JS cmd = unset;

    while(cursor < end)
    {
        uint32_t progress;

        cmd_old = cmd;
        cmd = *(cursor++);


        if(cmd_old != cmd){
            if(got_wlock){
                AtomicCompareExchange(&hmitree_wlock, 1, 0);
                got_wlock = 0;
            }
            if(got_rlock){
                AtomicCompareExchange(&hmitree_rlock, 1, 0);
                got_rlock = 0;
            }
        }
        switch(cmd)
        {
            case setval:
            {
                uint32_t index = *(uint32_t*)(cursor);
                uint8_t const *valptr = cursor + sizeof(uint32_t);


                if(index == heartbeat_index)
                    was_hearbeat = 1;

                if(index < HMI_ITEM_COUNT)
                {
                    hmi_tree_item_t *dsc = &hmi_tree_items[index];
                    size_t sz = 0;
                    void *dst_p = &rbuf[dsc->buf_index];

                    if(__Is_a_string(dsc)){
                        sz = ((STRING*)valptr)->len + 1;
                    } else {
                        UnpackVar(dsc, NULL, NULL, &sz);
                    }

                    if((valptr + sz) <= end)
                    {
                        // rescheduling spinlock until free
                        if(!got_rlock){
                            while(AtomicCompareExchange(&hmitree_rlock, 0, 1)){
                                nRT_reschedule();
                            }
                            got_rlock=1;
                        }

                        memcpy(dst_p, valptr, sz);

                        /* check that rstate is not already buf_set */
                        if(dsc->rstate != buf_set){
                            dsc->rstate = buf_set;
                            /* append entry to read list (changes from HMI) */
                            dsc->incoming_prev = incoming_tail;
                            incoming_tail = dsc;
                        }

                        progress = sz + sizeof(uint32_t) /* index */;
                    }
                    else
                    {
                        ret = -EINVAL;
                        goto exit_free;
                    }
                }
                else
                {
                    ret = -EINVAL;
                    goto exit_free;
                }
            }
            break;

            case reset:
            {
                progress = 0;
                if(!got_wlock){
                    while(AtomicCompareExchange(&hmitree_wlock, 0, 1)){
                        nRT_reschedule();
                    }
                    got_wlock = 1;
                }
                {
                    hmi_tree_item_t *dsc = subscriptions_tail;
                    while(dsc){
                        hmi_tree_item_t *_dsc = dsc->subscriptions_prev;
                        update_refresh_period(dsc, session_index, 0);
                        dsc = _dsc;
                    }
                }
            }
            break;

            case subscribe:
            {
                uint32_t index = *(uint32_t*)(cursor);
                uint16_t refresh_period_ms = *(uint32_t*)(cursor + sizeof(uint32_t));

                if(index < HMI_ITEM_COUNT)
                {
                    if(!got_wlock){
                        while(AtomicCompareExchange(&hmitree_wlock, 0, 1)){
                            nRT_reschedule();
                        }
                        got_wlock = 1;
                    }
                    hmi_tree_item_t *dsc = &hmi_tree_items[index];
                    update_refresh_period(dsc, session_index, refresh_period_ms);
                }
                else
                {
                    ret = -EINVAL;
                    goto exit_free;
                }

                progress = sizeof(uint32_t) /* index */ +
                           sizeof(uint16_t) /* refresh period */;
            }
            break;
            default:
                printf("svghmi_recv_dispatch unknown %%d\n",cmd);

        }
        cursor += progress;
    }
    ret = was_hearbeat;

exit_free:
    if(got_wlock){
        AtomicCompareExchange(&hmitree_wlock, 1, 0);
        got_wlock = 0;
    }
    if(got_rlock){
        AtomicCompareExchange(&hmitree_rlock, 1, 0);
        got_rlock = 0;
    }
    return ret;
}

