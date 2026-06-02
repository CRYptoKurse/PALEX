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
    mov rax, 0
    mov qword [rbp-8], rax
    mov rax, 1
    mov qword [rbp-16], rax
    mov rax, 0
    mov qword [rbp-24], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-32], rax
    mov rax, qword [rbp-32]
    cmp rax, 0
    je .Lmain_L_logical_false_3
    jmp .Lmain_L_rhs_1
.Lmain_L_rhs_1:
    mov rax, qword [rbp-24]
    mov qword [rbp-56], rax
    mov rax, qword [rbp-56]
    mov rbx, 0
    cqo
    idiv rbx
    mov qword [rbp-64], rax
    mov rax, qword [rbp-64]
    mov rbx, 0
    cmp rax, rbx
    setg al
    movzx rax, al
    mov qword [rbp-72], rax
    mov rax, qword [rbp-72]
    cmp rax, 0
    je .Lmain_L_logical_false_3
    jmp .Lmain_L_logical_true_2
.Lmain_L_logical_true_2:
    mov rax, 1
    mov qword [rbp-48], rax
    jmp .Lmain_L_logical_end_4
.Lmain_L_logical_false_3:
    mov rax, 0
    mov qword [rbp-48], rax
    jmp .Lmain_L_logical_end_4
.Lmain_L_logical_end_4:
    mov rax, qword [rbp-48]
    cmp rax, 0
    jne .Lmain_L_then_5
    jmp .Lmain_L_else_6
.Lmain_L_then_5:
    mov rax, 1
    jmp .Lmain_epilogue
.Lmain_L_else_6:
    jmp .Lmain_L_endif_7
.Lmain_L_endif_7:
    mov rax, qword [rbp-16]
    mov qword [rbp-80], rax
    mov rax, qword [rbp-80]
    cmp rax, 0
    jne .Lmain_L_logical_true_9
    jmp .Lmain_L_rhs_8
.Lmain_L_rhs_8:
    mov rax, qword [rbp-24]
    mov qword [rbp-96], rax
    mov rax, qword [rbp-96]
    mov rbx, 0
    cqo
    idiv rbx
    mov qword [rbp-104], rax
    mov rax, qword [rbp-104]
    mov rbx, 0
    cmp rax, rbx
    setg al
    movzx rax, al
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    cmp rax, 0
    jne .Lmain_L_logical_true_9
    jmp .Lmain_L_logical_false_10
.Lmain_L_logical_true_9:
    mov rax, 1
    mov qword [rbp-88], rax
    jmp .Lmain_L_logical_end_11
.Lmain_L_logical_false_10:
    mov rax, 0
    mov qword [rbp-88], rax
    jmp .Lmain_L_logical_end_11
.Lmain_L_logical_end_11:
    mov rax, qword [rbp-88]
    cmp rax, 0
    jne .Lmain_L_then_12
    jmp .Lmain_L_else_13
.Lmain_L_then_12:
    mov rax, 2
    jmp .Lmain_epilogue
.Lmain_L_else_13:
    jmp .Lmain_L_endif_14
.Lmain_L_endif_14:
    mov rax, 0
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
