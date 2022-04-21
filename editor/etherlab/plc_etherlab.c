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

/* Beremiz plugin functions */
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
%(slaves_initialization)s

    // extracting default value for not mapped entry in output PDOs
%(slaves_output_pdos_default_values_extraction)s

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

static RTIME _last_occur=0;
static RTIME _last_publish=0;
RTIME _current_lag=0;
RTIME _max_jitter=0;
static inline RTIME max(RTIME a,RTIME b){return a>b?a:b;}

void __publish_%(location)s(void)
{
%(publish_variables)s
    ecrt_domain_queue(domain1);
    {
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
    }
    ecrt_master_send(master);
    first_sent = 1;
}
