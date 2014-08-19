/*********************************************************************
 * @file          main.c
 * @version
 * @brief
 * @author        badnack <n.redini@gmail.com>
 * @date          Thu Nov 21 00:09:22 2013
 * Modified at:   Mon Dec  2 17:24:07 2013
 * Modified by:   badnack <n.redini@gmail.com>
 ********************************************************************/
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/wait.h>

#include "util.h"
#include "exit.h"
#include "errors.h"
#include "screens.h"
#include "dbhelper.h"

int clientsd = 0;
int listensd;
pid_t cleaner, main_process;

extern int user_id;

extern  Message send_poi(int);
void
kill_handler()
{
  if (getpid() != cleaner) {
    close(clientsd);
    close(listensd);
  }
  exit(0);
}

void
execute_service()
{
  int op;
  const char* err;

  while(1){
    send_main_screen();
    if ((op = recv_cmd()) <= 0) {
      err = (op) ? err_too_long : err_invalid_cmd;
      send_msg(err);
      break;
    }
    send_msg(ack_ok);
    if (f_array[op](user_id) < 0) {
      break;
    }
  }
  exit(0);
}

void
launch_cleaner()
{
  if (fork() == 0) {
    //cleaner
    cleaner = getpid();
    while (1) {
      sleep(CLEANER_WAIT_SEC);
      db_clean();
    }
  }
}

int
main(int argc, char* argv[])
{
  int reuse, status, i;
  socklen_t clilen;
  struct sockaddr_in server_addr, client_addr;
  pid_t c;

  if (argc <= 1) {
    fprintf(stderr, "Usage: %s [port]\n", argv[0]);
    exit(-1);
  }

  reuse = 1;
  signal(SIGKILL, kill_handler);
  signal(SIGINT, kill_handler);
  signal(SIGQUIT, kill_handler);

  main_process = getpid();
  init_system();
  launch_cleaner();

  if ((listensd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    perror("Error in creating a new socket");
    exit(2);
  }

  if (setsockopt(listensd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) == -1) {
    perror("setsockopt error");
    exit(1);
  }
  server_addr.sin_family = AF_INET;
  server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  server_addr.sin_port = htons(atoi(argv[1]));

  if (bind(listensd, (struct sockaddr*) &server_addr, sizeof(server_addr)) < 0) {
    perror("Error in binding a new socket");
    exit(-1);
  }

  if (listen(listensd, FORK_POOL)) {
    perror("Error on listen");
    exit(-1);
  }

  while (1) {
    clilen = sizeof(client_addr);
    if ((clientsd = accept(listensd, (struct sockaddr*) &client_addr, &clilen)) == -1) {
      perror("Fork has failed, connection has been dropped\n");
      sleep(1);
      continue;
    }

    if ((c = fork()) == -1) {
      perror("Fork has failed, connection has been dropped\n");
      sleep(1);
      continue;
    }

    if (c == 0) {
      close(listensd);
      execute_service();
    } else {
      close(clientsd);
      // clean dead childs
      i = 0;
      while (!waitpid(-1, &status, WNOHANG) && i < MAX_ZOMBIE_REMOVED){
        i++;
      }
    }
  }
  return 0;
}
