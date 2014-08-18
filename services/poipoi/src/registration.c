/*********************************************************************
 * @file          registration.c
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 21:13:28 2013
 * Modified at:   Fri Nov 29 10:33:21 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include "registration.h"
#include "dbhelper.h"
#include "my_poi.h"
#include "errors.h"

Message
send_registration(int v)
{
  int res=-1;
  char* buf;
  char username[MAX_USER_LEN], password[MAX_USER_LEN];
  Message retu, retp;

  send_msg("Registration form\n"              \
           "----------------------\n"         \
           "Inert your name: ");

  retu = recv_msg(username, MAX_USER_LEN);
  send_msg("\nInsert a Password: ");
  retp = recv_msg(password, MAX_USER_LEN);
  if (retu < 0 || retp < 0) {
    send_msg(err_invalid_cmd);
    return FATAL_ERROR;
  }

  if ((res = add_user(username, password)) < 0) {
    send_msg(err_already_exists);
    return WRONG_SELECTION;
  }
  
  send_msg(ack_ok);

   /* Create the output string, allocating enough memory to do that: (LENGTH of registered constant string) + (LENGTH of the username) + (length of the maximum rapresentable ineger in string format, so 10) + (terminator, so 1). */
  if ((buf = (char*) malloc(((strlen(registered) + strlen(username)) * sizeof(char)) + 11)) == NULL) {
    return FATAL_ERROR;
  }
  buf[0] = '\0';
  sprintf(buf, registered, res, username);
  send_msg(buf);
  free(buf);
  return res;
}
