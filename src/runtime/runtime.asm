section .bss
print_buffer: resb 32
read_buffer: resb 32

section .text
global print_int
global print_string
global read_int
global exit
global _start

print_int:
    push rbp
    mov rbp, rsp
    mov rax, rdi
    lea rsi, [print_buffer + 31]
    mov rcx, 0
    mov rbx, 0
    test rax, rax
    jge .pi_loop
    neg rax
    mov bl, 1
.pi_loop:
    xor rdx, rdx
    mov rdi, 10
    div rdi
    add dl, '0'
    dec rsi
    mov [rsi], dl
    inc rcx
    cmp rax, 0
    jne .pi_loop
    cmp bl, 1
    jne .pi_write
    dec rsi
    mov byte [rsi], '-'
    inc rcx
.pi_write:
    mov rax, 1
    mov rdi, 1
    mov rdx, rcx
    syscall
    pop rbp
    ret

print_string:
    push rbp
    mov rbp, rsp
    mov r8, rdi
    xor rcx, rcx
.ps_loop:
    mov al, [r8 + rcx]
    cmp al, 0
    je .ps_write
    inc rcx
    jmp .ps_loop
.ps_write:
    mov rax, 1
    mov rdi, 1
    mov rsi, r8
    mov rdx, rcx
    syscall
    pop rbp
    ret

read_int:
    push rbp
    mov rbp, rsp
    lea rsi, [read_buffer]
    mov rax, 0
    mov rdi, 0
    mov rdx, 31
    syscall
    cmp rax, 1
    jl .ri_fail
    mov rcx, rax
    mov rsi, read_buffer
    xor rax, rax
    xor rbx, rbx
    mov r8, 1
.ri_loop:
    cmp rcx, 0
    je .ri_done
    mov bl, [rsi]
    cmp bl, '-'
    je .ri_neg
    cmp bl, '+'
    je .ri_pos
    cmp bl, '0'
    jb .ri_done
    cmp bl, '9'
    ja .ri_done
    imul rax, 10
    sub bl, '0'
    add rax, rbx
    inc rsi
    dec rcx
    jmp .ri_loop
.ri_neg:
    mov r8, -1
    inc rsi
    dec rcx
    jmp .ri_loop
.ri_pos:
    inc rsi
    dec rcx
    jmp .ri_loop
.ri_done:
    cmp r8, 0
    jge .ri_return
    neg rax
.ri_return:
    pop rbp
    ret
.ri_fail:
    mov rax, 0
    pop rbp
    ret

exit:
    mov rax, 60
    syscall

_start:
    call main
    mov rdi, rax
    mov rax, 60
    syscall
