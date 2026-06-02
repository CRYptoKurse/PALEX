section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global subtract
subtract:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    mov qword [rbp-8], rdi
    mov qword [rbp-16], rsi
.Lsubtract_entry:
    mov rax, qword [rbp-8]
    mov qword [rbp-24], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-32], rax
    mov rax, qword [rbp-24]
    mov rbx, qword [rbp-32]
    sub rax, rbx
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    jmp .Lsubtract_epilogue
.Lsubtract_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 32
.Lmain_entry:
    ; PARAM 0 10
    ; PARAM 1 3
    mov rdi, 10
    mov rsi, 3
    call subtract
    mov qword [rbp-16], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-8], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
