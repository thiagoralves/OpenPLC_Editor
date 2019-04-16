#ifndef _BEREMIZ_H_
#define _BEREMIZ_H_

/* Beremiz' header file for use by extensions */

#include "iec_types.h"

#define LOG_LEVELS 4
#define LOG_CRITICAL 0
#define LOG_WARNING 1
#define LOG_INFO 2
#define LOG_DEBUG 3

extern unsigned long long common_ticktime__;

#ifdef TARGET_LOGGING_DISABLE
static inline int LogMessage(uint8_t level, char* buf, uint32_t size)
{
	(void)level;
	(void)buf;
	(void)size;
	return 0;
}
#else
int     LogMessage(uint8_t level, char* buf, uint32_t size);
#endif

long AtomicCompareExchange(long* atomicvar,long compared, long exchange);

#endif
