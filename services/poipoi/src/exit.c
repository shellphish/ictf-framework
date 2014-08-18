/*********************************************************************
 * @file          exit.c
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 00:20:14 2013
 * Modified at:   Mon Dec  2 17:38:18 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include "exit.h"

Message
send_exit(int v)
{
  send_msg("\n"\
           " ____   ___ ___   ____   ___ ___ \n"                        \
           "|  _ \\ / _ \\_ _| |  _ \\ / _ \\_ _|\n"                    \
           "| |_) | | | | |  | |_) | | | | | \n"                        \
           "|  __/| |_| | |  |  __/| |_| | | \n"                        \
           "|_|    \\___/___| |_|    \\___/___|\n"                      \
           "--------------------------------------\n\n"                 \
           "Are you sure you want to exit [y/n]: ");

  switch(recv_cmd()) {
  case FATAL_ERROR:
  case 7:
    //exit
    return BYE_BYE;
  case 8:
    break;
  default:
    send_pag_help(UNKNOWN);
    break;
  }
  return OK;
}
