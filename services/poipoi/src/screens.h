/*********************************************************************
 * @file          screens.h
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Fri Nov 22 17:37:44 2013
 * Modified at:   Mon Dec  2 17:35:26 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/


static char *screens[] = {"\n"
                          " ____   ___ ___   ____   ___ ___ \n"         \
                          "|  _ \\ / _ \\_ _| |  _ \\ / _ \\_ _|\n"         \
                          "| |_) | | | | |  | |_) | | | | | \n"         \
                          "|  __/| |_| | |  |  __/| |_| | | \n"         \
                          "|_|    \\___/___| |_|    \\___/___|\n"         \
                          "--------------------------------------\n\n"  \
                          "(R)egister to the service\n"                 \
                          "(L)og in\n"                                  \
                          "(G)et P.O.I.\n"                              \
                          "(A)dd new P.O.I.\n"                          \
                          "(H)elp\n"                                    \
                          "(E)xit\n"                                    \
                          "?>"};


void send_main_screen();
void send_my_account_screen();
