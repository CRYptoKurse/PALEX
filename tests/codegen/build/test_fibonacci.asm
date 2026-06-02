section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global fibonacci
fibonacci:
    push rbp
    mov rbp, rsp
    sub rsp, 96
    mov qword [rbp-8], rdi
.Lfibonacci_entry:
    mov rax, qword [rbp-8]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-16]
    mov rbx, 1
    cmp rax, rbx
    setle al
    movzx rax, al
    mov qword [rbp-32], rax
    mov rax, qword [rbp-32]
    cmp rax, 0
    jne .Lfibonacci_L_then_1
    jmp .Lfibonacci_L_else_2
.Lfibonacci_L_then_1:
    mov rax, qword [rbp-8]
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    jmp .Lfibonacci_epilogue
.Lfibonacci_L_else_2:
    jmp .Lfibonacci_L_endif_3
.Lfibonacci_L_endif_3:
    mov rax, qword [rbp-8]
    mov qword [rbp-48], rax
    mov rax, qword [rbp-48]
    mov rbx, 1
    sub rax, rbx
    mov qword [rbp-56], rax
    ; PARAM 0 t5
    mov rdi, qword [rbp-56]
    call fibonacci
    mov qword [rbp-64], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-72], rax
    mov rax, qword [rbp-72]
    mov rbx, 2
    sub rax, rbx
    mov qword [rbp-80], rax
    ; PARAM 0 t8
    mov rdi, qword [rbp-80]
    call fibonacci
    mov qword [rbp-88], rax
    mov rax, qword [rbp-64]
    mov rbx, qword [rbp-88]
    add rax, rbx
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    jmp .Lfibonacci_epilogue
.Lfibonacci_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 16
.Lmain_entry:
    ; PARAM 0 6
    mov rdi, 6
    call fibonacci
    mov qword [rbp-8], rax
    mov rax, qword [rbp-8]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
