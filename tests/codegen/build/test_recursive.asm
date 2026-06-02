section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global factorial
factorial:
    push rbp
    mov rbp, rsp
    sub rsp, 64
    mov qword [rbp-8], rdi
.Lfactorial_entry:
    mov rax, qword [rbp-8]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-16]
    mov rbx, 1
    cmp rax, rbx
    setle al
    movzx rax, al
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    cmp rax, 0
    jne .Lfactorial_L_then_1
    jmp .Lfactorial_L_else_2
.Lfactorial_L_then_1:
    mov rax, 1
    jmp .Lfactorial_epilogue
.Lfactorial_L_else_2:
    mov rax, qword [rbp-8]
    mov qword [rbp-32], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    mov rbx, 1
    sub rax, rbx
    mov qword [rbp-48], rax
    ; PARAM 0 t5
    mov rdi, qword [rbp-48]
    call factorial
    mov qword [rbp-56], rax
    mov rax, qword [rbp-32]
    mov rbx, qword [rbp-56]
    imul rax, rbx
    mov qword [rbp-64], rax
    mov rax, qword [rbp-64]
    jmp .Lfactorial_epilogue
.Lfactorial_L_endif_3:
.Lfactorial_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 16
.Lmain_entry:
    ; PARAM 0 5
    mov rdi, 5
    call factorial
    mov qword [rbp-8], rax
    mov rax, qword [rbp-8]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
