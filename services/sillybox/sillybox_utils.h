#ifndef INC_SILLYBOX_UTILS
#define INC_SILLYBOX_UTILS

#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <signal.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


#define DOUBLESTRINGIFY_(x) __STRING(x)
#define S__LINE__ DOUBLESTRINGIFY_(__LINE__)
#define V_ERR_PRINT(s) if (write(2, s, strlen(s)) == -1) { exit(-10); }
#define V(x) if (__builtin_expect(!!!(x), 0)) do { V_ERR_PRINT("FAILED at " __FILE__ ":" S__LINE__ ", it's not " #x "\n"); exit(-9); } while (0)
#define VE(x) if (__builtin_expect(!!!(x), 0)) do { perror("VE FAILED"); V_ERR_PRINT("FAILED at " __FILE__ ":" S__LINE__ ", it's not " #x "\n"); exit(-9); } while (0)

static inline void do_sleep(int seconds)
{
    while (seconds > 0)
        seconds = sleep(seconds);
}

static inline ssize_t do_read(int fd, uint8_t* obuf, uint32_t len)
{
    int r;
    uint8_t *buf = obuf;
    do {
        VE( (r = read(fd, buf, len)) >= 0 );
        if (r == 0) return buf - obuf;
        len -= r;
        buf += r;
    } while (len != 0);
    return buf - obuf;
}

static inline int do_waitpid(pid_t pid, int *pstatus)
{
    int r;
    while ((r = waitpid(pid, pstatus, 0)) == -1)
        VE(errno == EINTR);
    return r;
}

#endif /* INC_SILLYBOX_UTILS */
