#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sillybox_utils.h"

#define MAX_TIME 3   /* seconds before SIGTERM */
#define TERM_TIME 1  /* seconds between SIGTERM and SIGKILL */

int main(int argc, char *argv[])
{
    VE( signal(SIGPIPE, SIG_IGN) != SIG_ERR );
    VE(argc == 2);

    unsigned long long upid;
    V( sscanf(argv[1], "%llu", &upid) == 1 );
    pid_t box_pid = upid;

    do_sleep(MAX_TIME);

    kill(box_pid, SIGTERM);
    do_sleep(TERM_TIME);
    kill(box_pid, SIGKILL); VE((errno == 0) || (errno == ESRCH));

    waitpid(box_pid, NULL, WNOHANG);
    return 0;
}
