section .text
global _start
extern print_int
extern print_string
extern read_int
extern exit

global print_number
print_number:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    mov qword [rbp-8], rdi
.Lprint_number_entry:
    jmp .Lprint_number_epilogue
.Lprint_number_epilogue:
    mov rsp, rbp
    pop rbp
    ret

global main
main:
    push rbp
    mov rbp, rsp
    sub rsp, 16
.Lmain_entry:
    ; PARAM 0 42
    mov rdi, 42
    call print_number
    mov qword [rbp-8], rax
    mov rax, 0
    jmp .Lmain_epilogue
.Lmain_epilogue:
    mov rsp, rbp
    pop rbp
    ret
