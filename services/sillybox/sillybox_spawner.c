#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/prctl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sillybox_utils.h"

#define MY_ADDR "0.0.0.0"
#define MY_PORT 4669u


static void spawn_timekiller_for(pid_t box_pid, int sockfd)
{
    pid_t pid = fork();
    VE(pid != -1);

    char box_pid_string[100];
    int r = snprintf(box_pid_string, sizeof(box_pid_string), "%llu", (unsigned long long) box_pid);
    VE(((size_t) r) < sizeof(box_pid_string));

    if (pid != 0) { return; }

    close(sockfd);

    /* Sillyboxes cannot run for more than some time - this guy is the enforcer. */
    execl(MY_PATH "/sillybox_timekiller", MY_PATH "/sillybox_timekiller", box_pid_string, (char*) NULL);

    perror("Could not exec the timekiller!");
    VE(0);
}

static void spawn_sillybox(int sockfd)
{
    pid_t pid = fork();
    if (pid == -1) { V_ERR_PRINT("ERROR: could not fork!"); return; }
    if (pid != 0) { close(sockfd); return; }

    spawn_timekiller_for(getpid(), sockfd);

    dup2(sockfd, 0);
    dup2(sockfd, 1);
    dup2(sockfd, 2);
    close(sockfd);

    char *envp[] = { NULL };
    execle(MY_PATH "/sillybox", MY_PATH "/sillybox", (char*) NULL, envp);

    perror("Could not exec the sillybox!");
    VE(0);
}

int main()
{
    VE( signal(SIGPIPE, SIG_IGN) != SIG_ERR );
    VE( prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0 );

    int s = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    VE(s != -1);

    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    VE( inet_aton(MY_ADDR, &sa.sin_addr) != 0 );
    sa.sin_port = htons(MY_PORT);
    sa.sin_family = AF_INET;
    VE( bind(s, (const struct sockaddr *) &sa, sizeof(sa)) == 0 );

    int on = 1;
    VE( setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on)) == 0 );

    VE( listen(s, SOMAXCONN) == 0 );

    int as;
    while ((as = accept(s, NULL, NULL)) != -1)
        spawn_sillybox(as);
    VE(as != -1);
    return -1;
}
