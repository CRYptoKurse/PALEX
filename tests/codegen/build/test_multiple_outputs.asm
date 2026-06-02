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
    sub rsp, 112
.Lmain_entry:
    mov rax, 1
    mov qword [rbp-8], rax
    mov rax, 0
    mov qword [rbp-16], rax
    mov rax, 1
    mov qword [rbp-16], rax
    mov rax, 1
    mov qword [rbp-24], rax
    jmp .Lmain_L_for_cond_1
.Lmain_L_for_cond_1:
    mov rax, qword [rbp-16]
    mov qword [rbp-48], rax
    mov rax, qword [rbp-48]
    mov rbx, 5
    cmp rax, rbx
    setle al
    movzx rax, al
    mov qword [rbp-56], rax
    mov rax, qword [rbp-56]
    cmp rax, 0
    jne .Lmain_L_for_body_2
    jmp .Lmain_L_for_end_3
.Lmain_L_for_body_2:
    mov rax, qword [rbp-8]
    mov qword [rbp-64], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-72], rax
    mov rax, qword [rbp-64]
    mov rbx, qword [rbp-72]
    imul rax, rbx
    mov qword [rbp-80], rax
    mov rax, qword [rbp-80]
    mov qword [rbp-8], rax
    mov rax, qword [rbp-80]
    mov qword [rbp-88], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-96], rax
    mov rax, qword [rbp-96]
    mov rbx, 1
    add rax, rbx
    mov qword [rbp-104], rax
    mov rax, qword [rbp-104]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-104]
    mov qword [rbp-32], rax
    jmp .Lmain_L_for_cond_1
.Lmain_L_for_end_3:
    mov rax, qword [rbp-8]
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
