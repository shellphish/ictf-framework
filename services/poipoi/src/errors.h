/*********************************************************************
 * @file          errors.h
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Fri Nov 22 15:47:26 2013
 * Modified at:   Thu Nov 28 17:12:06 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/

#ifndef __ERRORS_H
#define __ERRORS_H

static const char err_undefined [] = "Undefined error occurred.";
static const char err_too_long [] = "Protocol error. Too many chars provided.";
static const char err_invalid_cmd [] = "Invalid requested operation.";
static const char err_not_logged [] = "You have to log on to the system first.";
static const char err_not_exists [] = "Incorrect User Id or Password.";
static const char err_already_exists [] = "User already exists.";
static const char err_invalid_info [] = "Some information you provided are not correct";
static const char err_too_poi [] = "Maximum number of P.O.I. reached.";

static const char no_poi [] = "You have no P.O.I. saved.";
static const char registered [] = "Sucessfully registered, your user ID is <%d>, your username is \"%s\". To log in use your ID.";
static const char welcome_back [] = "Welcome back %s!";
static const char ack_ok [] = "ACK_OK";
static const char end_of_list [] = "END_OK";

#endif
