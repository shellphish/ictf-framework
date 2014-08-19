/*********************************************************************
 * @file          help.c
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 19:58:57 2013
 * Modified at:   Mon Dec  2 19:18:05 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include "help.h"
#include "errors.h"

Message
send_pag_help(int page)
{
  int ret;
  char cmd_name[4];

  switch (page) {
  case 9:
    send_msg("\nUranium mining is the process of extraction of uranium ore from the ground.\n\n" \
             "A prominent use of uranium from mining is as fuel for building your nuclear weapons\n" \
             "and then terrifying your enemies. \n"                     \
             "The POIPOI service collects information of all uranium mines in the world, so if you\n" \
             "know of some new mines please insert related locations as soon as you can and help your\n" \
             "country to dominate the world!\n");
    break;
  case 1:
    send_msg("\nLog on to manage your personal account..\n");
    break;
  case 2:
    send_msg("\nRegister to POIPOI.\n");
    break;
  case 3:
    send_msg("\nHelp, what else you need to know?\n");
    break;
  case 4:
    send_msg("\nExit, what else you need to know?\n");
    break;
  case 5:
    send_msg("\nGet your spotted caves.\n");
    break;
  case 6:
    send_msg("\nAdd a new cave location.\n");
    break;
  case UNKNOWN:
  default:
    send_msg("\nFunctionality not found, please insert the first three letters of the " \
             "name:\n");
    if (recv_msg(cmd_name, MAX_USER_LEN) < 0) {
      send_msg(err_too_long);
      return FATAL_ERROR;
    }
    if ((ret = get_func_id((char*)cmd_name)) != UNKNOWN){
      send_pag_help(ret);
    } else {
      send_msg("Functionality does not exist.");
      return WRONG_SELECTION;
    }
  }
  return OK;
}

Message
send_help(int v)
{
  int pag_help;

  send_msg("\nWhich functionality do you need help for [T/L/R/H/E/G/A]: ");
  if ((pag_help = recv_cmd()) < 0) {
    send_msg(err_too_long);
    return WRONG_SELECTION;
  }

  if (pag_help == 8 || pag_help == 7 || pag_help == UNKNOWN) {
    send_msg(err_invalid_cmd);
    return WRONG_SELECTION;
  }
  send_msg(ack_ok);
  return send_pag_help(pag_help);
}
