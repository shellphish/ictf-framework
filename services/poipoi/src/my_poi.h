/*********************************************************************
 * @file          my_poi.h
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 20:41:30 2013
 * Modified at:   Mon Nov 25 20:06:51 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include <stdio.h>

#include "util.h"

#ifndef __MY_POI_H
#define __MY_POI_H

extern int logged, user_id;
extern char* username, *password;

Message send_login(int);
Message add_poi(int);
Message send_poi(int);

#endif
