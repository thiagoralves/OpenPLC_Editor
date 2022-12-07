/*

Template C code used to produce target Ethercat C code

Copyright (C) 2011-2014: Laurent BESSARD, Edouard TISSERANT

Distributed under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

See COPYING file for copyrights details.

*/

#include <rtdm/rtdm.h>
#include <native/task.h>
#include <native/timer.h>

#include "ecrt.h"

#include "beremiz.h"
#include "iec_types_all.h"

// declaration of interface variables
%(located_variables_declaration)s

// process data
uint8_t *domain1_pd = NULL;
%(used_pdo_entry_offset_variables_declaration)s

const static ec_pdo_entry_reg_t domain1_regs[] = {
%(used_pdo_entry_configuration)s
    {}
};

// Distributed Clock variables;
%(dc_variable)s
unsigned long long comp_period_ns = 500000ULL;

int comp_count = 1;
int comp_count_max;

#define DC_FILTER_CNT          1024

// EtherCAT slave-time-based DC Synchronization variables.
static uint64_t dc_start_time_ns = 0LL;
static uint64_t dc_time_ns = 0;
static uint8_t  dc_started = 0;
static int32_t  dc_diff_ns = 0;
static int32_t  prev_dc_diff_ns = 0;
static int64_t  dc_diff_total_ns = 0LL;
static int64_t  dc_delta_total_ns = 0LL;
static int      dc_filter_idx = 0;
static int64_t  dc_adjust_ns;
static int64_t  system_time_base = 0LL;

static uint64_t dc_first_app_time = 0LL;

unsigned long long frame_period_ns = 0ULL;

int debug_count = 0;
int slave_dc_used = 0;

void dc_init(void);
uint64_t system_time_ns(void);
RTIME system2count(uint64_t time);
void sync_distributed_clocks(void);
void update_master_clock(void);
RTIME calculate_sleeptime(uint64_t wakeup_time);
uint64_t calculate_first(void);

/*****************************************************************************/

%(pdos_configuration_declaration)s

long long wait_period_ns = 100000LL;

// EtherCAT
static ec_master_t *master = NULL;
static ec_domain_t *domain1 = NULL;
static int first_sent=0;
%(slaves_declaration)s
#define SLOGF(level, format, args...)\
{\
    char sbuf[256];\
    int slen = snprintf(sbuf , sizeof(sbuf) , format , ##args);\
    LogMessage(level, sbuf, slen);\
}

/* EtherCAT plugin functions */
int __init_%(location)s(int argc,char **argv)
{
    uint32_t abort_code;
    size_t result_size;
    
    abort_code = 0;
    result_size = 0;

    master = ecrt_request_master(%(master_number)d);
    if (!master) {
        SLOGF(LOG_CRITICAL, "EtherCAT master request failed!");
        return -1;
    }

    if(!(domain1 = ecrt_master_create_domain(master))){
        SLOGF(LOG_CRITICAL, "EtherCAT Domain Creation failed!");
        goto ecat_failed;
    }

    // slaves PDO configuration
%(slaves_configuration)s

    if (ecrt_domain_reg_pdo_entry_list(domain1, domain1_regs)) {
        SLOGF(LOG_CRITICAL, "EtherCAT PDO registration failed!");
        goto ecat_failed;
    }

    ecrt_master_set_send_interval(master, common_ticktime__);

    // slaves initialization
/*
%(slaves_initialization)s
*/
    // configure DC SYNC0/1 Signal
%(config_dc)s

    // select reference clock
#if DC_ENABLE
    {
        int ret;
        
        ret = ecrt_master_select_reference_clock(master, slave0);
        if (ret <0) {
            fprintf(stderr, "Failed to select reference clock : %%s\n",
                strerror(-ret));
            return ret;
        }
    }
#endif

    // extracting default value for not mapped entry in output PDOs
/*
%(slaves_output_pdos_default_values_extraction)s
*/

#if DC_ENABLE
    dc_init();
#endif

    if (ecrt_master_activate(master)){
        SLOGF(LOG_CRITICAL, "EtherCAT Master activation failed");
        goto ecat_failed;
    }

    if (!(domain1_pd = ecrt_domain_data(domain1))) {
        SLOGF(LOG_CRITICAL, "Failed to map EtherCAT process data");
        goto ecat_failed;
    }

    SLOGF(LOG_INFO, "Master %(master_number)d activated.");
    
    first_sent = 0;

    return 0;

ecat_failed:
    ecrt_release_master(master);
    return -1;

}

void __cleanup_%(location)s(void)
{
    //release master
    ecrt_release_master(master);
    first_sent = 0;
}

void __retrieve_%(location)s(void)
{
    // receive ethercat
    if(first_sent){
        ecrt_master_receive(master);
        ecrt_domain_process(domain1);
%(retrieve_variables)s
    }

}

/*
static RTIME _last_occur=0;
static RTIME _last_publish=0;
RTIME _current_lag=0;
RTIME _max_jitter=0;
static inline RTIME max(RTIME a,RTIME b){return a>b?a:b;}
*/

void __publish_%(location)s(void)
{
%(publish_variables)s
    ecrt_domain_queue(domain1);
    {
        /*
        RTIME current_time = rt_timer_read();
        // Limit spining max 1/5 of common_ticktime
        RTIME maxdeadline = current_time + (common_ticktime__ / 5);
        RTIME deadline = _last_occur ? 
            _last_occur + common_ticktime__ : 
            current_time + _max_jitter; 
        if(deadline > maxdeadline) deadline = maxdeadline;
        _current_lag = deadline - current_time;
        if(_last_publish != 0){
            RTIME period = current_time - _last_publish;
            if(period > common_ticktime__ )
                _max_jitter = max(_max_jitter, period - common_ticktime__);
            else
                _max_jitter = max(_max_jitter, common_ticktime__ - period);
        }
        _last_publish = current_time;
        _last_occur = current_time;
        while(current_time < deadline) {
            _last_occur = current_time; //Drift backward by default
            current_time = rt_timer_read();
        }
        if( _max_jitter * 10 < common_ticktime__ && _current_lag < _max_jitter){
            //Consuming security margin ?
            _last_occur = current_time; //Drift forward
        }
        */
    }

#if DC_ENABLE
    if (comp_count == 0)
        sync_distributed_clocks();
#endif

    ecrt_master_send(master);
    first_sent = 1;

#if DC_ENABLE
    if (comp_count == 0)
        update_master_clock();

    comp_count++;
    
    if (comp_count == comp_count_max)
        comp_count = 0;
#endif

}

/* Test Function For Parameter (SDO) Set */

/*
void GetSDOData(void){
    uint32_t abort_code, test_value;
    size_t result_size;
    uint8_t value[4];

    abort_code = 0;
    result_size = 0;
    test_value = 0;

    if (ecrt_master_sdo_upload(master, 0, 0x1000, 0x0, (uint8_t *)value, 4, &result_size, &abort_code)) {
        SLOGF(LOG_CRITICAL, "EtherCAT failed to get SDO Value");
        }
        test_value = EC_READ_S32((uint8_t *)value);
        SLOGF(LOG_INFO, "SDO Value %%d", test_value);
}
*/

int GetMasterData(void){
    master = ecrt_open_master(0);
    if (!master) {
        SLOGF(LOG_CRITICAL, "EtherCAT master request failed!");
        return -1;
    }
    return 0;
}

void ReleaseMasterData(void){
    ecrt_release_master(master);
}

uint32_t GetSDOData(uint16_t slave_pos, uint16_t idx, uint8_t subidx, int size){
    uint32_t abort_code, return_value;
    size_t result_size;
    uint8_t value[size];

    abort_code = 0;
    result_size = 0;

    if (ecrt_master_sdo_upload(master, slave_pos, idx, subidx, (uint8_t *)value, size, &result_size, &abort_code)) {
        SLOGF(LOG_CRITICAL, "EtherCAT failed to get SDO Value %%d %%d", idx, subidx);
    }

    return_value = EC_READ_S32((uint8_t *)value);
    //SLOGF(LOG_INFO, "SDO Value %%d", return_value);

    return return_value;
}

/*****************************************************************************/

void dc_init(void)
{
    slave_dc_used = 1;

    frame_period_ns = common_ticktime__;
    if (frame_period_ns <= comp_period_ns) {
        comp_count_max = comp_period_ns / frame_period_ns;
        comp_count = 0;
    } else  {
        comp_count_max = 1;
        comp_count = 0;
    }

    /* Set the initial master time */
    dc_start_time_ns = system_time_ns();
    dc_time_ns = dc_start_time_ns;

    /* by woonggy */
    dc_first_app_time = dc_start_time_ns;

    /*
     * Attention : The initial application time is also used for phase
     * calculation for the SYNC0/1 interrupts. Please be sure to call it at
     * the correct phase to the realtime cycle.
     */
    ecrt_master_application_time(master, dc_start_time_ns);
}

/****************************************************************************/

/*
 * Get the time in ns for the current cpu, adjusted by system_time_base.
 *
 * \attention Rather than calling rt_timer_read() directly, all application
 * time calls should use this method instead.
 *
 * \ret The time in ns.
 */
uint64_t system_time_ns(void)
{
    RTIME time = rt_timer_read();   // wkk

    if (unlikely(system_time_base > (SRTIME) time)) {
        fprintf(stderr, "%%s() error: system_time_base greater than"
                " system time (system_time_base: %%ld, time: %%llu\n",
                __func__, system_time_base, time);
        return time;
    }
    else {
        return time - system_time_base;
    }
}

/****************************************************************************/

// Convert system time to Xenomai time in counts (via the system_time_base).
RTIME system2count(uint64_t time)
{
    RTIME ret;

    if ((system_time_base < 0) &&
            ((uint64_t) (-system_time_base) > time)) {
        fprintf(stderr, "%%s() error: system_time_base less than"
                " system time (system_time_base: %%I64d, time: %%ld\n",
                __func__, system_time_base, time);
        ret = time;
    }
    else {
        ret = time + system_time_base;
    }

    return (RTIME) rt_timer_ns2ticks(ret); // wkk
}

/*****************************************************************************/

// Synchronise the distributed clocks
void sync_distributed_clocks(void)
{
    uint32_t ref_time = 0;
    RTIME prev_app_time = dc_time_ns;

    // get reference clock time to synchronize master cycle
    if(!ecrt_master_reference_clock_time(master, &ref_time)) {
        dc_diff_ns = (uint32_t) prev_app_time - ref_time;
    }
    // call to sync slaves to ref slave
    ecrt_master_sync_slave_clocks(master);
    // set master time in nano-seconds
    dc_time_ns = system_time_ns();
    ecrt_master_application_time(master, dc_time_ns);
}

/*****************************************************************************/

/*
 * Return the sign of a number
 * ie -1 for -ve value, 0 for 0, +1 for +ve value
 * \ret val the sign of the value
 */
#define sign(val) \
        ({ typeof (val) _val = (val); \
        ((_val > 0) - (_val < 0)); })

/*****************************************************************************/

/*
 * Update the master time based on ref slaves time diff
 * called after the ethercat frame is sent to avoid time jitter in
 * sync_distributed_clocks()
 */
void update_master_clock(void)
{
    // calc drift (via un-normalised time diff)
    int32_t delta = dc_diff_ns - prev_dc_diff_ns;
    prev_dc_diff_ns = dc_diff_ns;

    // normalise the time diff
    dc_diff_ns = dc_diff_ns >= 0 ?
            ((dc_diff_ns + (int32_t)(frame_period_ns / 2)) %%
                    (int32_t)frame_period_ns) - (frame_period_ns / 2) :
                    ((dc_diff_ns - (int32_t)(frame_period_ns / 2)) %%
                            (int32_t)frame_period_ns) - (frame_period_ns / 2) ;

    // only update if primary master
    if (dc_started) {
        // add to totals
        dc_diff_total_ns += dc_diff_ns;
        dc_delta_total_ns += delta;
        dc_filter_idx++;

        if (dc_filter_idx >= DC_FILTER_CNT) {
            dc_adjust_ns += dc_delta_total_ns >= 0 ?
                    ((dc_delta_total_ns + (DC_FILTER_CNT / 2)) / DC_FILTER_CNT) :
                    ((dc_delta_total_ns - (DC_FILTER_CNT / 2)) / DC_FILTER_CNT) ;

            // and add adjustment for general diff (to pull in drift)
            dc_adjust_ns += sign(dc_diff_total_ns / DC_FILTER_CNT);

            // limit crazy numbers (0.1%% of std cycle time)
            if (dc_adjust_ns < -1000) {
                dc_adjust_ns = -1000;
            }
            if (dc_adjust_ns > 1000) {
                dc_adjust_ns =  1000;
            }
            // reset
            dc_diff_total_ns = 0LL;
            dc_delta_total_ns = 0LL;
            dc_filter_idx = 0;
        }
        // add cycles adjustment to time base (including a spot adjustment)
        system_time_base += dc_adjust_ns + sign(dc_diff_ns);
    }
    else {
        dc_started = (dc_diff_ns != 0);

        if (dc_started) {
#if DC_ENABLE && DEBUG_MODE
            // output first diff
            fprintf(stderr, "First master diff: %%d\n", dc_diff_ns);
#endif
            // record the time of this initial cycle
            dc_start_time_ns = dc_time_ns;
        }
    }
}

/*****************************************************************************/

/*
 * Calculate the sleeptime
 */
RTIME calculate_sleeptime(uint64_t wakeup_time)
{
    RTIME wakeup_count = system2count (wakeup_time);
    RTIME current_count = rt_timer_read();

    if ((wakeup_count < current_count) || (wakeup_count > current_count + (50 * frame_period_ns)))  {
        fprintf(stderr, "%%s(): unexpected wake time! wc = %%lld\tcc = %%lld\n", __func__, wakeup_count, current_count);
    }

    return wakeup_count;
}

/*****************************************************************************/

/*
 * Calculate the sleeptime
 */
uint64_t calculate_first(void)
{
    uint64_t dc_remainder = 0LL;
    uint64_t dc_phase_set_time = 0LL;
    
    dc_phase_set_time = system_time_ns()+ frame_period_ns * 10;
    dc_remainder = (dc_phase_set_time - dc_first_app_time) %% frame_period_ns;

    return dc_phase_set_time + frame_period_ns - dc_remainder;
}

/*****************************************************************************/
