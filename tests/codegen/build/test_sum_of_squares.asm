section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global square
square:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    mov qword [rbp-8], rdi
.Lsquare_entry:
    mov rax, qword [rbp-8]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-24], rax
    mov rax, qword [rbp-16]
    mov rbx, qword [rbp-24]
    imul rax, rbx
    mov qword [rbp-32], rax
    mov rax, qword [rbp-32]
    jmp .Lsquare_epilogue
.Lsquare_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 112
.Lmain_entry:
    mov rax, 0
    mov qword [rbp-8], rax
    mov rax, 0
    mov qword [rbp-16], rax
    mov rax, 1
    mov qword [rbp-16], rax
    mov rax, 1
    mov qword [rbp-72], rax
    jmp .Lmain_L_for_cond_1
.Lmain_L_for_cond_1:
    mov rax, qword [rbp-16]
    mov qword [rbp-80], rax
    mov rax, qword [rbp-80]
    mov rbx, 5
    cmp rax, rbx
    setle al
    movzx rax, al
    mov qword [rbp-88], rax
    mov rax, qword [rbp-88]
    cmp rax, 0
    jne .Lmain_L_for_body_2
    jmp .Lmain_L_for_end_3
.Lmain_L_for_body_2:
    mov rax, qword [rbp-8]
    mov qword [rbp-96], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-104], rax
    ; PARAM 0 t8
    mov rdi, qword [rbp-104]
    call square
    mov qword [rbp-112], rax
    mov rax, qword [rbp-96]
    mov rbx, qword [rbp-112]
    add rax, rbx
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    mov qword [rbp-8], rax
    mov rax, qword [rbp-24]
    mov qword [rbp-32], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    mov rbx, 1
    add rax, rbx
    mov qword [rbp-48], rax
    mov rax, qword [rbp-48]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-48]
    mov qword [rbp-56], rax
    jmp .Lmain_L_for_cond_1
.Lmain_L_for_end_3:
    mov rax, qword [rbp-8]
    mov qword [rbp-64], rax
    mov rax, qword [rbp-64]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
