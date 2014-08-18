BITS 32

; This is not actually guaranteed to work in NASM...
#include <asm/unistd_32.h>


start:

    call tg
tg: pop edi

    mov eax, __NR_exit_group
    mov ebx, 22
    call [gs:0x10]
