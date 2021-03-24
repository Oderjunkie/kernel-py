import argparse
import sys
import ast
constcount = 0
data = []
code = []
registers = ['rcx', 'rdx', 'r8', 'r9'] + ['']*21
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
            global code
            if type(part.value)==ast.Call:
                subq = 0
                if len(part.value.args)>len(registers):
                    raise Exception('No more than {} arguments per function!'.format(len(registers)))
                if part.value.func.value.id=='stdio':
                    #print(list(zip(part.value.args)))
                    temp = []
                    for num, (arg, reg) in enumerate(zip(part.value.args, registers)):
                        if reg=='':
                            reg = subq+32
                            subq += 8
                        if type(arg.value)==str:
                            data.append('.LC{}: .asciz "{}"'.format(constcount, escape(arg.value)))
                            if num<4:
                                temp.append('leaq .LC{}(%rip), %{}'.format(constcount, reg))
                            else:
                                temp.append('leaq .LC{}(%rip), %rax'.format(constcount))
                                temp.append('movq %rax, {}(%rsp)'.format(reg))
                            constcount += 1
                        if type(arg.value)==float:
                            if num<4:
                                temp.append('movq ${}, %{}'.format(int(arg.value), reg))
                            else:
                                temp.append('movq ${}, %rax'.format(int(arg.value)))
                                temp.append('movq %rax, {}(%rsp)'.format(reg))
                        if type(arg.value)==int:
                            if num<4:
                                temp.append('movq ${}, %{}'.format(arg.value, reg))
                            else:
                                temp.append('movq ${}, %rax'.format(arg.value))
                                temp.append('movq %rax, {}(%rsp)'.format(reg))
                    if subq>0: code.append('subq ${}, %rsp'.format(subq))
                    code += temp
                    code.append('call {}'.format(part.value.func.attr))
                    if subq>0: code.append('addq ${}, %rsp'.format(subq))
        if type(part)==ast.Module: return parse_Module(part)
        if type(part)==ast.Import: return parse_Import(part)
        if type(part)==ast.ImportFrom: return parse_ImportFrom(part)
        if type(part)==ast.Expr: return parse_Expr(part)
        print(ast.dump(part))
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
