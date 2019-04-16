/*

Template C code used to produce target Ethercat C code.

Copyright (C) 2011-2014: Laurent BESSARD, Edouard TISSERANT

Distributed under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

See COPYING file for copyrights details.

*/

#include "iec_types_all.h"

#define FREE 0
#define ACQUIRED 1
#define ANSWERED 2

long SDOLock = FREE;
extern long AtomicCompareExchange(long* atomicvar,long compared, long exchange);

int AcquireSDOLock() {
	return AtomicCompareExchange(&SDOLock, FREE, ACQUIRED) == FREE;
}

void SDOAnswered() {
	AtomicCompareExchange(&SDOLock, ACQUIRED, ANSWERED);
}

int HasAnswer() {
	return SDOLock == ANSWERED;
}

void ReleaseSDOLock() {
	AtomicCompareExchange(&SDOLock, ANSWERED, FREE);
}

int __init_etherlab_ext()
{
    SDOLock = FREE;
    return 0;
}

void __cleanup_etherlab_ext()
{
}

void __retrieve_etherlab_ext()
{
}

void __publish_etherlab_ext()
{
}
