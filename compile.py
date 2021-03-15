import argparse
import sys
import ast
constcount = 0
data = []
code = []
registers = ['rcx', 'rdx', 'r8', 'r9']
def compiler(name):
    global constcount
    tree = ast.parse(open(name, 'r').read(), name, type_comments=True)
    def compiler_int(part):
        def parse_Import(part):
            if part.module=='libc':
                return
        def parse_ImportFrom(part):
            if part.module=='libc':
                return
        def parse_Module(part):
            for stmt in part.body:
                compiler_int(stmt)
        def escape(s):
            result = []
            for char in s:
                    result.append('\\%o' % ord(char))
            return ''.join(result)
        def parse_Expr(part):
            global constcount
            if type(part.value)==ast.Call:
                if len(part.value.args)>4:
                    raise Exception('No more than 4 arguments!')
                if part.value.func.value.id=='stdio':
                    for arg, reg in zip(part.value.args, registers):
                        if type(arg.value)==str:
                            data.append('.LC{}: .asciz "{}"'.format(constcount, escape(arg.value)))
                            code.append('leaq .LC{}(%rip), %{}'.format(constcount, reg))
                            constcount += 1
                        if type(arg.value)==float:
                            code.append('leaq ${}, %{}'.format(int(arg.value), reg))
                        if type(arg.value)==int:
                            code.append('leaq ${}, %{}'.format(arg.value, reg))
                    code.append('call {}'.format(part.value.func.attr))
        if type(part)==ast.Module: return parse_Module(part)
        if type(part)==ast.Import: return parse_Import(part)
        if type(part)==ast.ImportFrom: return parse_ImportFrom(part)
        if type(part)==ast.Expr: return parse_Expr(part)
        return True
    compiler_int(tree)
    codetext = '\n'.join(code)
    datatext = '\n'.join(data)
    out = '''.file "{}"
.section .rdata, "dr"
{}
.text
.globl main
main:
pushq %rbp
movq %rsp, %rbp
subq $32, %rsp
movl %ecx, 16(%rbp)
movq %rdx, 24(%rbp)
call __main
{}
movl $0, %eax
addq $32, %rsp
popq %rbp
ret'''.format(name, datatext, codetext)
    return out
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('string', metavar='in_file', type=str,
                        help='The input python file')
    parser.add_argument('-o', type=str, default='a.out',
                        help='The output assembly file.')
    args = parser.parse_args()
    with open(args.o, 'w') as f:
        f.write(compiler(args.string))
        f.close()
