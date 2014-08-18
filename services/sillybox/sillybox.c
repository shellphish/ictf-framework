#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/unistd.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/ptrace.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <sys/user.h>
#include <sys/wait.h>
#include <fcntl.h>
#include "sillybox_utils.h"


/* Packet format:
 * password len byte | password | raw binary code
 */

#define MAX_CODE_LEN 10000u

static uint8_t pwlen;
static char password[300];
static int (*code)();


/* Defines that are missing or misspelled in glibc's files. */
#define PTRACE_EVENT_SECCOMP    7
#define PTRACE_O_TRACESECCOMP   (1 << PTRACE_EVENT_SECCOMP)
#define PTRACE_O_EXITKILL       (1 << 20)


static void limit_syscalls()
{
#   define BPF_prohibit_syscall(name) \
        BPF_JUMP(BPF_JMP+BPF_K+BPF_JEQ, __NR_##name, 0, 1), \
        BPF_STMT(BPF_RET, SECCOMP_RET_KILL)

    struct sock_filter filters[] = {
        /* Loads the syscall number */
        BPF_STMT(BPF_LD+BPF_W+BPF_ABS, offsetof(struct seccomp_data, nr)),

        /* Here I limit which files engineers can open */
        BPF_JUMP(BPF_JMP+BPF_K+BPF_JEQ, __NR_open, 0, 1),
        BPF_STMT(BPF_RET, SECCOMP_RET_TRACE), /* Checked by allow_open() */

        /* sillybox handles all file opening stuff, so all those things are
         * prohibited! We are totally better!
         * If coders don't believe us, their code can crash, for all we care.
         * Also, engineers don't need super weird stuff, it's fine to prohibit
         * it. */
        BPF_prohibit_syscall(creat),
        BPF_prohibit_syscall(link),
        BPF_prohibit_syscall(unlink),
        BPF_prohibit_syscall(mknod),
        BPF_prohibit_syscall(chmod),
        BPF_prohibit_syscall(lchown),
        BPF_prohibit_syscall(rename),
        BPF_prohibit_syscall(mkdir),
        BPF_prohibit_syscall(rmdir),
        BPF_prohibit_syscall(dup),
        BPF_prohibit_syscall(pipe),
        BPF_prohibit_syscall(umount2),
        BPF_prohibit_syscall(ioctl),
        BPF_prohibit_syscall(fcntl),
        BPF_prohibit_syscall(dup2),
        BPF_prohibit_syscall(select),
        BPF_prohibit_syscall(symlink),
        BPF_prohibit_syscall(readlink),
        BPF_prohibit_syscall(uselib),
        BPF_prohibit_syscall(readdir),
        BPF_prohibit_syscall(mmap),
        BPF_prohibit_syscall(munmap),
        BPF_prohibit_syscall(truncate),
        BPF_prohibit_syscall(socketcall),
        BPF_prohibit_syscall(ipc),
        BPF_prohibit_syscall(getdents),
        BPF_prohibit_syscall(_newselect),
        BPF_prohibit_syscall(flock),
        BPF_prohibit_syscall(poll),
        BPF_prohibit_syscall(nfsservctl),
        BPF_prohibit_syscall(chown),
        BPF_prohibit_syscall(mmap2),
        BPF_prohibit_syscall(truncate64),
        BPF_prohibit_syscall(chown32),
        BPF_prohibit_syscall(fcntl64),
        BPF_prohibit_syscall(setxattr),
        BPF_prohibit_syscall(lsetxattr),
        BPF_prohibit_syscall(inotify_init),
        BPF_prohibit_syscall(inotify_add_watch),
        BPF_prohibit_syscall(inotify_rm_watch),
        BPF_prohibit_syscall(pselect6),
        BPF_prohibit_syscall(ppoll),
        BPF_prohibit_syscall(dup3),
        BPF_prohibit_syscall(pipe2),
        BPF_prohibit_syscall(inotify_init1),

        /* No killing others! That would be mean! */
        BPF_prohibit_syscall(kill),
        BPF_prohibit_syscall(tkill),
        BPF_prohibit_syscall(tgkill),

        /* All the rest is allowed! */
        BPF_STMT(BPF_RET, SECCOMP_RET_ALLOW),

        /* TODO_FOR_SILLYENGINEERS_TESTERS:
         * I don't know, maybe there is a bug. Or two.
         * Or, well, I don't know, maybe there are others out of here!
         * Oh, and remove this comment before giving this to customers, we
         * don't want accidents :)
         */
    };
    struct sock_fprog fprog = { sizeof(filters)/sizeof(filters[0]), filters };
    VE( prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fprog, 0) == 0 );
}

static void load_code()
{
    void *m = mmap(0, 4*4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    VE(m != MAP_FAILED);
    ssize_t real_code_len = do_read(0, m, MAX_CODE_LEN+1);
    V(real_code_len > 0);
    V(real_code_len <= MAX_CODE_LEN);
    VE( mprotect(m, 4*4096, PROT_READ|PROT_WRITE|PROT_EXEC) == 0 );

    uint8_t cd80[2] = { 0xCD, 0x80 };
    if (memmem(m, real_code_len, cd80, 2) != NULL) {
        fprintf(stderr, "LOL, who uses that thing do to syscalls these days?\n");
        V(0);
    }

    code = m;
}

static void load_password()
{
    do_read(0, &pwlen, 1);
    V(pwlen <= 50);
    do_read(0, (uint8_t*) password, pwlen);
    password[pwlen] = '\0';
}

#define CRYPTO_CMD "$6$4669$"
#define CRYPT_HLEN 86

static bool allow_reading(const char *filename)
{
    char *hash = crypt(password, CRYPTO_CMD);
    if (hash == NULL) return false;
    hash += strlen(CRYPTO_CMD);

    char stored_hash[CRYPT_HLEN];

    char pwname[250];
    sprintf(pwname, "%s.password", filename);
    int pwfd = open(pwname, O_RDONLY, 0600);
    if (pwfd == -1) return false;
    do_read(pwfd, (uint8_t*) stored_hash, CRYPT_HLEN);
    if (close(pwfd) != 0) return false;

    return (memcmp(hash, stored_hash, CRYPT_HLEN) == 0);
}

static bool allow_writing(const char *filename)
{
    char *hash = crypt(password, CRYPTO_CMD);
    if (hash == NULL) return false;
    hash += strlen(CRYPTO_CMD);

    char pwname[250];
    sprintf(pwname, "%s.password", filename);
    int pwfd = open(pwname, O_WRONLY|O_CREAT|O_EXCL, 0600);
    return (pwfd != -1)
        && (write(pwfd, hash, CRYPT_HLEN) == CRYPT_HLEN)
        && (fsync(pwfd) == 0)
        && (close(pwfd) == 0);
}

static bool allow_open(pid_t c, long pfilename, long flags, long mode)
{
    char filename[210]; /* There is a maximum allowed length */
    int ok = 0, i;
    for (i = 0; i < 200; ++i) {
        struct iovec local_iov = { .iov_base = &filename[i], .iov_len = 1 };
        struct iovec remote_iov = { .iov_base = (void*) (pfilename+i), .iov_len = 1 };
        int ret = process_vm_readv(c, &local_iov, 1, &remote_iov, 1, 0);
        if (ret != 1) { fprintf(stderr, "Failed readv - invalid pointer?\n"); return false; }
        if (filename[i] == '\0') { ok = 1; break; }
    }
    if (!ok)
        return false;

    /* Strings I use are not allowed in filenames */
    if (strcasestr(filename, "password") != NULL)
        return false;

    /* Check flags and the password */
    if (flags == O_RDONLY)
        return allow_reading(filename);
    if (flags == (O_WRONLY | O_CREAT | O_EXCL))
        return (mode == 0600) && allow_writing(filename);
    return false;
}

static int check_opens(pid_t c)
{
    close(0); /* Do not interfere with regular IO */
    close(1);
    close(2);

    int status, sig;
    if ( (do_waitpid(c, &status) != c) ||
         (!WIFSTOPPED(status)) ||
         (ptrace(PTRACE_SETOPTIONS, c, 0, PTRACE_O_EXITKILL | PTRACE_O_TRACESECCOMP) != 0))
    {
        kill(c, SIGKILL); /* Weird status, should not happen */
        VE(0);
    }

    /* We "sync" on raise(SIGSTOP) */
    sig = WSTOPSIG(status);
    while (sig != SIGSTOP)
        VE( ptrace(PTRACE_CONT, c, 0, sig) == 0 );
    VE( ptrace(PTRACE_CONT, c, 0, 0) == 0 );

    while (do_waitpid(c, &status) == c) {
        if (WIFEXITED(status)) return 0;
        if (WIFSIGNALED(status)) return 0;
        V(WIFSTOPPED(status));

        sig = WSTOPSIG(status);
        siginfo_t si;
        VE( ptrace(PTRACE_GETSIGINFO, c, 0, &si) == 0 );

        if (sig != SIGTRAP) {
            VE( ptrace(PTRACE_CONT, c, 0, sig) == 0 );
            continue;
        }

        if ((status>>8) != (SIGTRAP | (PTRACE_EVENT_SECCOMP<<8))) {
            VE( ptrace(PTRACE_CONT, c, 0, (si.si_code == SI_KERNEL) ? 0 : sig) == 0 );
            continue;
        }

        struct user_regs_struct regs;
        VE( (ptrace(PTRACE_GETREGS, c, 0, &regs) == 0) || (errno == ESRCH) );
        if (errno == ESRCH) {
            continue;
        }

        if (regs.orig_eax != __NR_open) {
            kill(c, SIGKILL); /* Again, unexpected */
            V(0);
        }

        /* This is the open() check */
        if (!allow_open(c, regs.ebx, regs.ecx, regs.edx)) {
            kill(c, SIGKILL);
            return -7;
        }

        VE( ptrace(PTRACE_CONT, c, 0, 0) == 0 );
    }
    return -5;
}

int main(int argc, char *argv[])
{
    /* Note: I need a kernel >= 3.8. Yes, I am lazy. */

    if (argc == 2) { /* Just for testing */
        int ifd = open(argv[1], O_RDONLY); VE(ifd != -1);
        dup2(ifd, 0);
        close(ifd);
    }

    VE( signal(SIGPIPE, SIG_IGN) != SIG_ERR );
    VE( prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0 );

    load_password();
    load_code();
    shutdown(0, SHUT_RD); /* No more input is needed */

    /* Start the tracer for open() */
    pid_t pid = fork();
    VE(pid != -1);
    if (pid != 0)
        return check_opens(pid);

    /* Make sure the tracer is active */
    VE( ptrace(PTRACE_TRACEME, 0, 0, 0) == 0 );
    VE( raise(SIGSTOP) == 0 );

    /* Here we go! */
    limit_syscalls();

    return code();
}
