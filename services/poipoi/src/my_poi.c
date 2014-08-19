/*********************************************************************
 * @file          my_poi.c
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 20:42:50 2013
 * Modified at:   Mon Dec  2 17:40:00 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include "my_poi.h"
#include "errors.h"
#include "screens.h"
#include "dbhelper.h"

int logged = 0, user_id = -1;
char delimiter = ':';

Message
send_poi(int id)
{
  POI *list;
  int tot, i, n, count;
  // max char per text + max len double * 2 + 3 delimiters
  char buff[((MAX_USER_LEN + 1) + (11 * 2) +  3) * MAX_POI_PER_USER + 1];

  n = 0;
  if (id == -1) {
    send_msg(err_not_logged);
    return NOT_LOGGED;
  }
  if ((tot = list_poi(id, &list)) < 0) {
    send_msg(err_undefined);
    return FATAL_ERROR;
  }

  send_msg(ack_ok);

  count = 0;
  for (i = 0; i < tot; i++) {
    /* latitude */
    if ((n = snprintf(&buff[count], 11 + 1 + 1, "%f%c", list[i].lat, delimiter)) < 0 ||
        n > MAX_USER_LEN) {
      return FATAL_ERROR;
    }

    count += n;
    /* longitude */
    if ((n = snprintf(&buff[count], 11 + 1 + 1, "%f%c", list[i].lon, delimiter)) < 0 ||
        n > MAX_USER_LEN) {
      return FATAL_ERROR;
    }
    count += n;
    if ((n = snprintf(&buff[count], MAX_USER_LEN + 1, "%s\n", list[i].descr)) < 0 ||
        n > MAX_USER_LEN) {
      return FATAL_ERROR;
    }

    count += n;
  }
  buff[count] = '\0';

  if (!tot) {
    if ((n = snprintf(buff, strlen(no_poi), "%s", no_poi)) < 0 ||
        n > strlen(no_poi) + 1) {
      return FATAL_ERROR;
    }
  }

  send_msg(buff);
  return OK;
}

int
is_valid_point(double latitude, double longitude)
{
  if (latitude > 90 || latitude < -90) {
    return 0;
  }

  if (longitude > 180 || longitude < -180) {
    return 0;
  }
  return 1;
}

Message
add_poi(int v)
{
  char recv_data[MAX_USER_LEN];
  char *err_latitude, *err_longitude;
  double latitude, longitude;
  int set1, set2, set3, len;
  int ret;

  if (!logged) {
    send_msg(err_not_logged);
    return NOT_LOGGED;
  }
  send_msg(ack_ok);

  send_msg("\n"\
           " ____   ___ ___   ____   ___ ___ \n"                        \
           "|  _ \\ / _ \\_ _| |  _ \\ / _ \\_ _|\n"                    \
           "| |_) | | | | |  | |_) | | | | | \n"                        \
           "|  __/| |_| | |  |  __/| |_| | | \n"                        \
           "|_|    \\___/___| |_|    \\___/___|\n"                      \
           "--------------------------------------\n\n"                 \
           "Insert latitude [Signed degrees format (DDD.dddd)]: ");

  set1 = 0;
  set2 = 0;
  set3 = 0;

  if (recv_msg(recv_data, MAX_USER_LEN) == OK) {
    latitude = strtod(recv_data, &err_latitude);
    len = strnlen(recv_data, MAX_USER_LEN);
    set1 = (&recv_data[len] == err_latitude);
  }
  send_msg("\nInsert longitude [Signed degrees format (DDD.dddd)]: ");
  if (recv_msg(recv_data, MAX_USER_LEN) == OK) {
    longitude = strtod(recv_data, &err_longitude);
    len = strnlen(recv_data, MAX_USER_LEN);
    set2 = (&recv_data[len] == err_longitude);
  }
  send_msg("\nInsert description of the P.O.I.: ");
  if (recv_msg(recv_data, MAX_USER_LEN) == OK) {
    set3 = 1;
  }

  /* if some error occurred */
  if (!(set1 & set2 & set3) ||
      !is_valid_point(latitude, longitude)) {
    send_msg(err_invalid_info);
    return WRONG_SELECTION;
  }
  if ((ret = insert_poi(user_id, latitude, longitude, recv_data)) < 0) {
    if (ret == DB_ERROR_TOO_MANY_POIS) {
      send_msg(err_too_poi);
    } else {
      send_msg(err_undefined);
    }
    return FATAL_ERROR;
  }
  send_msg(ack_ok);
  send_msg("P.O.I. successfully inserted.");

  return OK;
}

Message
send_login(int v)
{
  int uid, len;
  char userid[MAX_USER_LEN], password[MAX_USER_LEN], *tmp, *buf;
  Message retu, retp;

  send_msg("\n"\
           " ____   ___ ___   ____   ___ ___ \n"                        \
           "|  _ \\ / _ \\_ _| |  _ \\ / _ \\_ _|\n"                    \
           "| |_) | | | | |  | |_) | | | | | \n"                        \
           "|  __/| |_| | |  |  __/| |_| | | \n"                        \
           "|_|    \\___/___| |_|    \\___/___|\n"                      \
           "--------------------------------------\n\n"                 \
           "User Id: ");
  retu = recv_msg(userid, MAX_USER_LEN);
  send_msg("\nPassword: ");
  retp = recv_msg(password, MAX_USER_LEN);

  if (retu < 0 || retp < 0) {
    send_msg(err_invalid_cmd);
    return FATAL_ERROR;
  }

  uid = strtol(userid, &tmp, 10);
  len = strnlen(userid, MAX_USER_LEN);

  if (tmp != &userid[len] || (check_cred(uid, password, &tmp) < 0)) {
    send_msg(err_not_exists);
    return WRONG_SELECTION;
  }
  if (tmp == NULL) {
    send_msg(err_undefined);
    return FATAL_ERROR;
  }

  if ((buf = (char*) malloc(((strlen(welcome_back) + strlen(tmp)) * sizeof(char)) + 1)) == NULL) {
    send_msg(err_undefined);
    return FATAL_ERROR;
  }
  sprintf(buf, welcome_back, tmp);

  user_id = uid;
  logged = 1;
  send_msg(ack_ok);
  send_msg(buf);
  free(buf);
  free(tmp);
  return OK;
}
