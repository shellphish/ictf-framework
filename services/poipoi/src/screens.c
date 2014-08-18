/*********************************************************************
 * @file          screens.c
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Fri Nov 22 17:43:15 2013
 * Modified at:   Tue Nov 26 00:05:44 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include "screens.h"
#include "util.h"

void
send_main_screen()
{
  send_msg(screens[0]);
}
