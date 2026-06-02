section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global add
add:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    mov qword [rbp-8], rdi
    mov qword [rbp-16], rsi
.Ladd_entry:
    mov rax, qword [rbp-8]
    mov qword [rbp-24], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-32], rax
    mov rax, qword [rbp-24]
    mov rbx, qword [rbp-32]
    add rax, rbx
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    jmp .Ladd_epilogue
.Ladd_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 16
.Lmain_entry:
    ; PARAM 0 2
    ; PARAM 1 3
    mov rdi, 2
    mov rsi, 3
    call add
    mov qword [rbp-8], rax
    mov rax, qword [rbp-8]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
