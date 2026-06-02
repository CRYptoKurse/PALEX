section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global isPrime
isPrime:
    push rbp
    mov rbp, rsp
    sub rsp, 144
    mov qword [rbp-8], rdi
.LisPrime_entry:
    mov rax, qword [rbp-8]
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    mov rbx, 2
    cmp rax, rbx
    setl al
    movzx rax, al
    mov qword [rbp-72], rax
    mov rax, qword [rbp-72]
    cmp rax, 0
    jne .LisPrime_L_then_1
    jmp .LisPrime_L_else_2
.LisPrime_L_then_1:
    mov rax, 0
    jmp .LisPrime_epilogue
.LisPrime_L_else_2:
    jmp .LisPrime_L_endif_3
.LisPrime_L_endif_3:
    mov rax, 2
    mov qword [rbp-16], rax
    jmp .LisPrime_L_while_cond_4
.LisPrime_L_while_cond_4:
    mov rax, qword [rbp-16]
    mov qword [rbp-80], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-88], rax
    mov rax, qword [rbp-80]
    mov rbx, qword [rbp-88]
    imul rax, rbx
    mov qword [rbp-96], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-104], rax
    mov rax, qword [rbp-96]
    mov rbx, qword [rbp-104]
    cmp rax, rbx
    setle al
    movzx rax, al
    mov qword [rbp-112], rax
    mov rax, qword [rbp-112]
    cmp rax, 0
    jne .LisPrime_L_while_body_5
    jmp .LisPrime_L_while_end_6
.LisPrime_L_while_body_5:
    mov rax, qword [rbp-8]
    mov qword [rbp-120], rax
    mov rax, qword [rbp-16]
    mov qword [rbp-128], rax
    mov rax, qword [rbp-120]
    mov rbx, qword [rbp-128]
    cqo
    idiv rbx
    mov rax, rdx
    mov qword [rbp-32], rax
    mov rax, qword [rbp-32]
    mov rbx, 0
    cmp rax, rbx
    sete al
    movzx rax, al
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    cmp rax, 0
    jne .LisPrime_L_then_7
    jmp .LisPrime_L_else_8
.LisPrime_L_then_7:
    mov rax, 0
    jmp .LisPrime_epilogue
.LisPrime_L_else_8:
    jmp .LisPrime_L_endif_9
.LisPrime_L_endif_9:
    mov rax, qword [rbp-16]
    mov qword [rbp-48], rax
    mov rax, qword [rbp-48]
    mov rbx, 1
    add rax, rbx
    mov qword [rbp-56], rax
    mov rax, qword [rbp-56]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-56]
    mov qword [rbp-64], rax
    jmp .LisPrime_L_while_cond_4
.LisPrime_L_while_end_6:
    mov rax, 1
    jmp .LisPrime_epilogue
.LisPrime_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 48
.Lmain_entry:
    mov rax, 0
    mov qword [rbp-8], rax
    ; PARAM 0 7
    mov rdi, 7
    call isPrime
    mov qword [rbp-16], rax
    mov rax, qword [rbp-16]
    cmp rax, 0
    jne .Lmain_L_then_10
    jmp .Lmain_L_else_11
.Lmain_L_then_10:
    mov rax, 1
    mov qword [rbp-8], rax
    mov rax, 1
    mov qword [rbp-24], rax
    jmp .Lmain_L_endif_12
.Lmain_L_else_11:
    mov rax, 0
    mov qword [rbp-8], rax
    mov rax, 0
    mov qword [rbp-32], rax
    jmp .Lmain_L_endif_12
.Lmain_L_endif_12:
    mov rax, qword [rbp-8]
    mov qword [rbp-40], rax
    mov rax, qword [rbp-40]
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
