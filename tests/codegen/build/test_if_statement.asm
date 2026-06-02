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
    sub rsp, 32
.Lmain_entry:
    mov rax, 5
    mov qword [rbp-8], rax
    mov rax, qword [rbp-8]
    mov qword [rbp-16], rax
    mov rax, qword [rbp-16]
    mov rbx, 3
    cmp rax, rbx
    setg al
    movzx rax, al
    mov qword [rbp-24], rax
    mov rax, qword [rbp-24]
    cmp rax, 0
    jne .Lmain_L_then_1
    jmp .Lmain_L_else_2
.Lmain_L_then_1:
    mov rax, 1
    jmp .Lmain_epilogue
.Lmain_L_else_2:
    mov rax, 0
    jmp .Lmain_epilogue
.Lmain_L_endif_3:
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
