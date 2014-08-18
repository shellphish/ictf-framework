/*********************************************************************
 * @file          util.h
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 00:11:39 2013
 * Modified at:   Mon Dec  2 18:54:43 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <time.h>

#ifndef __TSUTIL_H
#define __TSUTIL_H

#define FORK_POOL 50
#define CHILD_ITER 50
#define MAX_USER_LEN 50
#define MAX_USER_LIMIT 17000
#define DATA_VALIDITY_INTERVAL 900// 15 min
#define CLEANER_WAIT_SEC 1200
#define MAX_ZOMBIE_REMOVED 50

typedef enum Message Message;
enum Message {
  BYE_BYE         = -6,
  NOT_LOGGED      = -5,
  TOO_LONG        = -4,
  WRONG_SELECTION = -3,
  FATAL_ERROR     = -2,
  UNKNOWN         =  0,
  OK              =  1
};


extern int clientsd;
Message (*f_array[7])(int);

void init_system();
int get_func_id(char*);
int get_code_opt(char);
Message send_msg(const char*);
Message recv_msg(char*, int);
int recv_cmd();
Message send_bytes(unsigned char*, int);

#endif
