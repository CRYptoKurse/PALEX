section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 64
.Lmain_entry:
    mov rax, 2
    mov qword [rbp-8], rax
    mov rax, 0
    mov qword [rbp-16], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    mov rbx, 1
    cmp rax, rbx
    setg al
    movzx rax, al
    mov qword [rbp-32], rax
    mov rax, qword [rbp-32]
    cmp rax, 0
    jne .Lmain_L_then_1
    jmp .Lmain_L_else_2
.Lmain_L_then_1:
    mov rax, 10
    mov qword [rbp-16], rax
    mov rax, 10
    mov qword [rbp-40], rax
    jmp .Lmain_L_endif_3
.Lmain_L_else_2:
    mov rax, 20
    mov qword [rbp-16], rax
    mov rax, 20
    mov qword [rbp-48], rax
    jmp .Lmain_L_endif_3
.Lmain_L_endif_3:
    mov rax, qword [rbp-16]
    mov qword [rbp-56], rax
    mov rax, qword [rbp-56]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
