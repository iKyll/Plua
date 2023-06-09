from dataclasses import dataclass
from typing import *
from enum import Enum, auto
import sys

Loc = Tuple[str, int, int]
 
class OpType(Enum):
    PRINT=auto()
    LPAREN=auto()
    RPAREN=auto()
    PLUS=auto()
    MUL=auto()
    FLOAT=auto()
    TRUEDIV=auto()
    SUB=auto()
    GT=auto()
    LT=auto()
    GE=auto()
    LE=auto()
    EQUAL=auto()
    DEF=auto()
    TYPE_EQUAL=auto()
    EQUAL_ARROW=auto()
    FUNC=auto()
    END=auto()
    ARG_ARROW=auto()
    #LBRACKET=auto()
    #RBRACKET=auto()

OpTypes = [ x for x in OpType if x ]

SEPARATORS = ['(', ')']
KEYWORDS_SIGNS = ['+', '*', '/', '-', '>', '<', '>=', '<=', '==', ':', '=>', '<-']
KEYWORDS = [ str(typ).split('.')[1].lower() for typ in OpType]
KEYWORDS_BY_NAME = {
        "print": OpType.PRINT,
        "("    : OpType.LPAREN,
        ")"    : OpType.RPAREN,
        "+"    : OpType.PLUS,
        "*"    : OpType.MUL,
        "float": OpType.FLOAT,
        "/"    : OpType.TRUEDIV,
        "-"    : OpType.SUB,
        ">"    : OpType.GT,
        "<"    : OpType.LT,
        ">="   : OpType.GE,
        "<="   : OpType.LE,
        "=="   : OpType.EQUAL,
        "def"  : OpType.DEF,
        ":"    : OpType.TYPE_EQUAL,
        "=>"   : OpType.EQUAL_ARROW,
        "func" : OpType.FUNC,
        "end"  : OpType.END,
        "<-"   : OpType.ARG_ARROW
    }
assert len(KEYWORDS_BY_NAME) == len(OpType), "Exhaustive handling of ops type in KEYWORDS_BY_NAME"
assert len(KEYWORDS_SIGNS) == len(OpType) - 7, "Exhaustive handling of keywords signs"
assert len(SEPARATORS) == len(OpType) - 17, "Exhaustive handling of SEPARATORS"

@dataclass
class Op:
    typ: OpType
    loc: Loc
    value: Union[str, int, list]

class TokenType(Enum):
    KEYWORD=auto()
    WORD=auto()
    LPAREN=auto()
    RPAREN=auto()
    STR=auto()
    INT=auto()
    FLOAT=auto()
    BOOL=auto()

TokenTypes = [ x for x in TokenType if x ]

@dataclass
class Token:
    typ: TokenType
    loc: Loc
    value: Union[str, int]

@dataclass
class Parens:
    # Loc of left paren
    loc: Loc
    ops: Union[Token, Op]

    def __len__(self):
        length = 0
        ip = 0
        op = None
        while ip < len(self.ops):
            if op and isinstance(op, Parens): 
                length += len(Parens)
                ip += 1
            op = self.ops[ip]
            if op.typ == OpType.PRINT: 
                length += calculate_length_ops(op.value)
                ip += 1
            elif op.typ in TokenTypes or op.typ in OpTypes: 
                ip += 1
                length += 1
        return length

@dataclass
class Variable:
    typ: Union[TokenType.INT, TokenType.FLOAT, TokenType.BOOL, TokenType.STR]
    value: Token

Program = List[Union[Token, Op, Parens]]

Variables = {}
# List because assignation is just first, second etc. No names are required
Context_Variables = []
Functions = {}


def simulate(program: Program, was_arg: bool=False, track_usage: bool=False, in_function: bool=False):
    global Context_Variables

    in_parens = False
    if isinstance(program, Parens):
        program = program.ops
        in_parens = True

    if in_function and len(Context_Variables) > 0:
        assigned = {}
        ip = 0
        if len(program) > 0:
            for idx, token in enumerate(program):
                if isinstance(token, Parens):
                    for jdx, op in enumerate(token.ops):
                        if op.typ == TokenType.WORD:
                            if op.value in assigned:
                                token.ops[jdx] = assigned[op]
                            elif op.value not in Variables and op.value not in Functions:
                                assigned = {op.value: Context_Variables[ip]}
                                token.ops[jdx] = Context_Variables[ip]
                                ip += 1
                elif token.typ == TokenType.WORD:
                    if token.value in assigned:
                        program[idx] = assigned[token]
                    elif token.value not in Variables and token.value not in Functions:
                        assigned = {token.value: Context_Variables[ip]}
                        program[idx] = Context_Variables[ip]
                        ip += 1
 
    used = 0
    ip = 0
    while ip < len(program):
    #for op in range(len(program)):
        if len(program) == 0: break
        if ip < 0: ip = 0
        if isinstance(program, Parens): program = program.ops
        token = program[ip]
        #print("Executing: ", token.typ, " Program is now: ", program, " Ip is :", ip)
        if token.typ in OpType:
            assert len(OpType) == 19, "Exhaustive handling of ops in simulate()"
            if token.typ == OpType.PRINT:
                value = program[ip+1]

                program.pop(ip)
                program.pop(ip)

                if isinstance(value, Parens):
                    value = simulate(value, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for print operator: ", value)
                        exit(1)
                    # Doesn't crash ?
                    value = value[0].value 

                elif (hasattr(value, 'typ') and value.typ == TokenType.WORD):
                    value = simulate([value], was_arg=True, track_usage=False, in_function=in_function).value

                elif (hasattr(value, 'typ')):
                    value = value.value
                if isinstance(value, str):
                    print(value.encode('latin-1', 'backslashreplace').decode('unicode-escape'))
                else:
                    print(value)
                used += 1
                if was_arg: return None, 0
                continue
            elif token.typ == OpType.FLOAT:
                _ = program.pop(ip)
                arg = program.pop(ip)
                used += 2
                
                if arg.typ != TokenType.INT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected an integer but found: ", arg.typ)
                    exit(1)

                if ip == 0 or ip == 1:
                    eff_ip = 2
                else: eff_ip = ip
                program.insert(eff_ip-2, Token(TokenType.FLOAT, arg.loc, float(arg.value)))
                continue
            elif token.typ == OpType.PLUS:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd
 
                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `+` operator can only add two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ == TokenType.KEYWORD:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `+` operator can only add strings or numbers.")
                    exit(1)
                new_value = arg1.value + arg2.value

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(arg1.typ, arg2.loc, new_value))
                else: return Token(arg1.typ, arg2.loc, new_value), used
            elif token.typ == OpType.MUL:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0].value

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0].value


                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `*` operator can only multiply two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `*` operator can only multiply numbers but found type: `{arg1.typ}`")
                    exit(1)
                new_value = arg1.value * arg2.value

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(arg1.typ, arg2.loc, new_value))
                else: return Token(arg1.typ, arg2.loc, new_value), used
            elif token.typ == OpType.TRUEDIV:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `/` operator can only multiply two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `/` operator can only multiply numbers but found type: `{arg1.typ}`")
                    exit(1)

                if arg1.value == 0 or arg2.value == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `/` operator cannot divide by 0")
                    exit(1)
                new_value = arg1.value / arg2.value

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(TokenType.FLOAT, arg2.loc, new_value))
                else: return Token(TokenType.FLOAT, arg2.loc, new_value), used
            elif token.typ == OpType.SUB:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `-` operator can only substract two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `-` operator can only substract numbers but found type: `{arg1.typ}`")
                    exit(1)
                new_value = arg1.value - arg2.value

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(arg1.typ, arg2.loc, new_value))
                else: return Token(arg1.typ, arg2.loc, new_value), used
            elif token.typ == OpType.GT:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `>` operator can only return a boolean value if the arguments have the same type but found:  `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `>` operator can only checks for numbers but found type: `{arg1.typ}`")
                    exit(1)

                new_value = (arg1.value > arg2.value)

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(TokenType.BOOL, arg2.loc, new_value))
                else: return Token(TokenType.BOOL, arg2.loc, new_value), used
            elif token.typ == OpType.LT:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `<` operator can only return a boolean value if the arguments have the same type but found:  `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `<` operator can only checks for numbers but found type: `{arg1.typ}`")
                    exit(1)
                new_value = True if arg1.value < arg2.value else False

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(TokenType.BOOL, arg2.loc, new_value))
                else: return Token(TokenType.BOOL, arg2.loc, new_value), used
            elif token.typ == OpType.GE:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `>=` operator can only return a boolean value if the arguments have the same type but found:  `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `>=` operator can only checks for numbers but found type: `{arg1.typ}`")
                    exit(1)
                new_value = True if arg1.value >= arg2.value else False

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(TokenType.BOOL, arg2.loc, new_value))
                else: return Token(TokenType.BOOL, arg2.loc, new_value), used
            elif token.typ == OpType.LE:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"
    
                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `<=` operator can only return a boolean value if the arguments have the same type but found:  `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT and arg1.typ != TokenType.FLOAT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `<=` operator can only checks for numbers but found type: `{arg1.typ}`")
                    exit(1)
                new_value = True if arg1.value <= arg2.value else False

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(TokenType.BOOL, arg2.loc, new_value))
                else: return Token(TokenType.BOOL, arg2.loc, new_value), used
            elif token.typ == OpType.EQUAL:
                if ip == 0:
                    assert False, f"This could be a bug in either the parser or the inserts placed in the simulation, Current program is: {program}"
                if ip == 1 or ip == 2:
                    placing_ip = 0
                else: placing_ip = ip - 3
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                used += 3
                if arg2 == token: 
                    assert False, "ERROR?"

                if isinstance(arg1, Parens):
                    arg1 = simulate(arg1, track_usage=False)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg1)
                        exit(1)
                    arg1 = arg1[0]

                if isinstance(arg2, Parens):
                    arg2 = simulate(arg2, track_usage=False)
                    if len(arg2) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for mul operator: ", arg2)
                        exit(1)
                    arg2 = arg2[0]

                if arg2.typ in OpType:
                    program.insert(ip-1, arg2)
                    result = simulate(program[placing_ip:], was_arg=True, track_usage=True)

                    arg2, usedd = result
                    for i in range(used): 
                        if program: program.pop(ip-1)
                    if not was_arg: used += usedd

                if isinstance(arg2, tuple): arg2 = arg2[0]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `==` operator can only return a boolean value if the arguments have the same type but found:  `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                new_value = True if arg1.value == arg2.value else False

                ip -= 2
                if not was_arg: program.insert(placing_ip, Token(TokenType.BOOL, arg2.loc, new_value))
                else: return Token(TokenType.BOOL, arg2.loc, new_value), used
            elif token.typ == OpType.DEF:
                _ = program.pop(ip)
                name = program.pop(ip)
                if name.typ != TokenType.WORD:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: trying to name a variable to either a keyword, a number or a boolean value.")
                    exit(1)

                type_equal = program.pop(ip)
                if type_equal.typ != OpType.TYPE_EQUAL:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected `:` but found: ", type_equal.value)
                    exit(1)
                typ = program.pop(ip)
                typ = simulate([type_equal, typ], was_arg=True, track_usage=False)

                equal_arrow = program.pop(ip)
                if equal_arrow.typ != OpType.EQUAL_ARROW:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected `=>` but found: ", type_equal.value)
                    exit(1)
                value = program.pop(ip)
                value = simulate([equal_arrow, value], was_arg=True, track_usage=False)
    
                if typ != value.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: mismatched type definition and type of value.")
                    exit(1)
                Variables[name.value] = value
            elif token.typ == OpType.TYPE_EQUAL:
                if len(program[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument but found nothing.")
                    exit(1)
                _ = program.pop(ip)
                value = program.pop(ip).value
                if value == 'int': return TokenType.INT
                elif value == 'float': return TokenType.FLOAT
                elif value == 'bool': return TokenType.BOOL
                elif value == 'str': return TokenType.STR
                print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: given type is not a correct type.")
                exit(1)
            elif token.typ == OpType.EQUAL_ARROW:
                if isinstance(program[ip+1], Parens): return simulate(program[ip+1], was_arg=True, track_usage=False)
                return simulate([program[ip+1]], was_arg=True, track_usage=False)
            elif token.typ == OpType.FUNC:
                assert False, "Parser error?"
            elif token.typ == OpType.END:
                assert False, "Parser error?"
            elif token.typ == OpType.ARG_ARROW:
                assert False, "Parser error?"
        elif token.typ == TokenType.WORD:
            if in_function:
                print(program)
                exit(1)
            elif token.value in Variables:
                if not was_arg and program[ip+1].typ == OpType.EQUAL_ARROW:
                    if len(program[ip+1:]) == 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: not enough arguments for variable reassignation.")
                        exit(1)

                    value = simulate(program[ip+1:ip+3])
            
                    program.pop(ip)
                    program.pop(ip)
                    program.pop(ip)

                    if value.typ != Variables[token.value].typ:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: variable reassignation cannot change variable type.")
                        exit(1)
                    Variables[token.value] = value
                else: 
                    program[ip] = Variables[token.value]
            elif token.value in Functions:
                func = Functions[token.value]
                if func["args"]:
                    args_len = len(func["args_name"])
                    if len(program[ip:]) == 1:
                        print("%s:%d:%d: ERROR: expected arg for function call but found nothing" % token.loc)
                        exit(1)
                    
                    arg = program[ip+1]
                    if not isinstance(arg, Parens):
                        print("%s:%d:%d: ERROR: arguments need to be passed in parentheses for function call" % token.loc)
                        exit(1)

                    if args_len < len(arg):
                        print("%s:%d:%d: ERROR: too many arguments for function call" % token.loc)
                        exit(1)
                    elif args_len > len(arg):
                        print("%s:%d:%d: ERROR: not enough arguments for function call" % token.loc)
                        exit(1)

                    for v in arg.ops:
                        Context_Variables.append(v)
                    simulate(Functions[token.value]["ops"], in_function=True)
                    Context_Variables = []
                    program.pop(ip)
                else: simulate(Functions[token.value]["ops"])
                program.pop(ip)
            else:
                print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: unknown word: `{token.value}`")
                exit(1)
        elif token.typ in TokenType:
            ip += 1 

    if len(program) != 0:
        if in_parens: 
            if track_usage: return program, used
            return program
        if was_arg:
            if len(program) == 1: 
                if track_usage: return program[0], used
                return program[0]
            if track_usage: return program, used
            return program
        token = program.pop()
        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: unhandled argument in program: `{token.value}` with type: `{token.typ}`")
        exit(1)

# Implement the brackets
def find_last_separator(program: Program) -> int:
    if len(program) == 0:
        print("ERROR: find_last_separator had an empty list")
        exit(1)
    if program[0].typ == TokenType.RPAREN: return 0
    if program[0].typ != TokenType.LPAREN:
        print("ERROR: first argument in find_last_separator need to be a separator")
        exit(1)
    needed = 1
    ip = 1
    for op in program[1:]:
        if op.typ == TokenType.LPAREN: needed += 1
        elif op.typ == TokenType.RPAREN:
            needed -= 1
            if needed == 0:
                return ip + 1 
        ip += 1
    # Find a way to get token's loc
    print(f"ERROR: parentheses not closed, missing: {needed} parentheses")
    exit(1)


# Token can pass solo as args
def calculate_length_ops(ops: Program) -> int:
    if isinstance(ops, Parens): return len(ops)
    elif isinstance(ops, Token): return 1
    elif isinstance(ops, Op): return 1
    length = 0
    ip = 0
    op = None
    while ip < len(ops):
        if op and isinstance(op, Parens): 
            length += len(Parens)
            ip += 1
        op = ops[ip]
        if op.typ == OpType.PRINT: 
            length += calculate_length_ops(op.value) + 1
            ip += 1
        elif op.typ in TokenTypes or op.value in KEYWORDS or op.value in KEYWORDS_SIGNS or op.value in SEPARATORS: 
            ip += 1
            length += 1
    return length

def parse_token_as_op(tokens: List[Token], func: bool=False) -> Program:
    ip = 0
    end_tokens = []
    for op in range(len(tokens)):
        if len(tokens) == 0: return end_tokens
        if ip > len(tokens) - 1: return end_tokens
        token = tokens[ip]
        for separator in SEPARATORS:
            if token.value == separator:
                loc = token.loc
                closing_index = find_last_separator(tokens[ip:])
                value = parse_token_as_op(tokens[ip+1:ip+closing_index])
                if len(value) == 0: 
                    ip += 1
                    continue
                if tokens[ip:] == 1:
                    return Parens(loc, value)
                end_tokens.insert(ip, Parens(loc, value))
                closing_index = find_last_separator(tokens[ip:])
                ip += closing_index      
        if token.value in KEYWORDS or token.value in KEYWORDS_SIGNS:
            typ = KEYWORDS_BY_NAME[token.value]
            assert len(OpType) == 19, "Exhaustive handling of ops in parse_token_as_op()"
            if typ == OpType.PRINT:
                if len(tokens[ip:]) == 1:
                    print("%s:%d:%d: ERROR: expected argument but found nothing " % token.loc)
                    exit(1)
                #arg = tokens[ip+1]
                #closing_index = 0
                #if arg.typ == TokenType.LPAREN:
                #    closing_index = find_last_separator(tokens[ip+1:])
                #    arg = parse_token_as_op(tokens[ip+1:ip+closing_index+1])
                #    ip += closing_index
                #else: ip += 1

                #if isinstance(arg, Parens): end_tokens.append(Op(OpType.PRINT, token.loc, arg))
                #else:
                #    if (hasattr(arg, 'typ') and arg.typ != TokenType.STR) and (hasattr(arg, 'typ') and arg.typ != TokenType.INT) and (hasattr(arg, 'typ') and arg.typ != TokenType.WORD):
                #        print(f"{arg.loc[0]}:{arg.loc[1]}:{arg.loc[2]}: ERROR: expected string, number or variable name but found `{arg.typ}`")
                #        exit(1)
                # Indent this and change `None` to `arg`
                end_tokens.append(Op(OpType.PRINT, token.loc, None))
                ip += 1
            elif typ == OpType.FLOAT:
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.FLOAT, token.loc, None))
                ip += 1
            elif typ == OpType.PLUS:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.PLUS, token.loc, None))
                ip += 1
            elif typ == OpType.MUL:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.MUL, token.loc, None))
                ip += 1
            elif typ == OpType.TRUEDIV:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.TRUEDIV, token.loc, None))
                ip += 1
            elif typ == OpType.SUB:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.SUB, token.loc, None))
                ip += 1 
            elif typ == OpType.GT:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.GT, token.loc, None))
                ip += 1
            elif typ == OpType.LT:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.LT, token.loc, None))
                ip += 1
            elif typ == OpType.GE:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.GE, token.loc, None))
                ip += 1
            elif typ == OpType.LE:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.LE, token.loc, None))
                ip += 1
            elif typ == OpType.EQUAL:
                if ip == 0:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                end_tokens.append(Op(OpType.EQUAL, token.loc, None))
                ip += 1
            elif typ == OpType.DEF:
                if len(tokens[ip:]) < 6:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: not enough arguments for the variable definition.")
                    exit(1)
                end_tokens.append(Op(OpType.DEF, token.loc, None))
                ip += 1
            elif typ == OpType.TYPE_EQUAL:
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: not enough arguments for the type equal operator.")
                    exit(1)
                end_tokens.append(Op(OpType.TYPE_EQUAL, token.loc, None))
                ip += 1
            elif typ == OpType.EQUAL_ARROW:
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: not enough arguments for the arrow operator.")
                    exit(1)
                end_tokens.append(Op(OpType.EQUAL_ARROW, token.loc, None))
                ip += 1
            elif typ == OpType.FUNC:
                ops = []
                i = ip
                while i < len(tokens):
                    if tokens[i].typ == TokenType.KEYWORD:
                        if tokens[i].value == 'end': break
                    i += 1
                # Don't forget end keyword
                i += 1

                if i < 4:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: not enough arguments for the func operator.")
                    exit(1)

                ip += 1 # Skip func operator
                i -= 1

                name = tokens[ip]
                if name.typ != TokenType.WORD:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: naming a function with either a keyword, a number or a string is not allowed.")
                    exit(1)
                ip += 1 # Skip name
                i -= 1
            
                ops = parse_token_as_op(tokens[ip:ip+i], func=True)
                length = calculate_length_ops(tokens[ip:ip+i])     

                ip += length
                i -= length
                assert i == 0, f"Parser error? : {i}"

                if isinstance(ops, Parens): 
                    ops = ops.ops
                    if tokens[ip-1].typ != OpType.END and tokens[ip-1].value != 'end':
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: function assignation not ended.")
                        exit(1)
                    # To bait the pop
                    ops.append(None)
                elif ops[-1].typ != OpType.END:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: function assignation not ended.")
                    exit(1)

                argument = False
                if ops[0].typ == OpType.ARG_ARROW:
                    argument = True
                    func_args = []
                    if not isinstance(ops[1], Parens):
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: wrong argument type")
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: NOTE: functions arguments need to be passed in Parentheses.")
                        exit(1)
                    
                    args = ops[1].ops
                    if len(ops[1:]) == 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: not enough arguments for the func operator.")
                        exit(1)

                    func_ops = ops[2:]
                    for idx, arg in enumerate(args):
                        if isinstance(arg, Parens):
                            print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: wrong argument type")
                            print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: NOTE: arguments can't be Parens, Keywords, Strings or numbers")
                            exit(1)
                        # Modify check to verify passed argument is not func name or variable
                        elif arg.typ != TokenType.WORD:
                            print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: wrong argument type")
                            print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: NOTE: arguments can't be Parens, Keywords, Strings or numbers")
                            exit(1)

                        found = False
                        for op in func_ops[:-1]:
                            if isinstance(op, Parens):
                                for oop in op.ops:
                                    if oop.value == arg.value:
                                        found = True
                            elif op.value == arg.value:
                                found = True
                        if not found:
                            print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: argument is defined in function but unused.")
                            exit(1)
                        func_args.append(arg)
                        args.pop(idx)
                    ops = ops[2:]
                ops.pop()
        
                if argument:
                    Functions[name.value] = { "args": True, "args_name": func_args, "ops": ops } 
                else:
                    Functions[name.value] = { "args": False, "ops": ops }
            elif typ == OpType.END:
                end_tokens.append(Op(OpType.END, token.loc, "func"))
                ip += 1

                if func: return end_tokens
            elif typ == OpType.ARG_ARROW:
                end_tokens.append(Op(OpType.ARG_ARROW, token.loc, "func"))
                ip += 1
        elif token.typ in [TokenType.STR, TokenType.INT, TokenType.FLOAT, TokenType.BOOL, TokenType.WORD]:
            end_tokens.append(token)
            ip += 1
    return end_tokens

def find_token_type(value: str):
    if value in KEYWORDS or value in KEYWORDS_SIGNS:
        return TokenType.KEYWORD
    elif value in SEPARATORS:
        # Change that later (When brackets come too)
        return TokenType.PAREN
    else:
        try:
            int(value)
            return TokenType.INT
        except ValueError:
            try:
                float(value)
                return TokenType.FLOAT
            except ValueError:
                return TokenType.WORD

def find_index(line: str, start, space=True, quotes=False):
    if quotes:
        while start < len(line) and line[start] != '"':
            start += 1
        return start
    if space:
        while start < len(line) and line[start].isspace():
            start += 1
        return start
    while start < len(line) and not line[start].isspace():
        start += 1
    return start

def lex_line(line: str) -> Tuple[int, TokenType, Union[str, int]]:
    col = find_index(line, 0)
    while col < len(line):
        if line[col] == '(':
            yield (col, TokenType.LPAREN, '(')
            col = find_index(line, col + 1)
        elif line[col] == ')':
            yield (col, TokenType.RPAREN, ')')
            col = find_index(line, col + 1)
        elif line[col] == '"':
            end_word = find_index(line, col+1, space=False, quotes=True) 
            if line[end_word] != '"': assert False, "Lexer error ?"
            yield (col, TokenType.STR, line[col+1:end_word])
            col = find_index(line, end_word+1)
        else:
            end_word = find_index(line, col+1, space=False)
            value = line[col:end_word]
            typ = find_token_type(value)
            if typ == TokenType.INT: value = int(value)
            elif typ == TokenType.FLOAT: value = float(value)
            yield (col, typ, value)
            col = find_index(line, end_word+1)

def lex_file(filepath: str) -> List[Token]:
    with open(filepath, "r") as file:
        tokens_ = [(filepath, row, col, typ, value)
                for (row, line) in enumerate(file.readlines())
                for (col, typ, value) in lex_line(line)]
    return handle_raw_tokens(tokens_)

def handle_raw_tokens(tokens_: list) -> List[Token]:
    toks = []
    for token_ in tokens_:
        (filepath, row, col, typ, value) = token_
        loc = (filepath, row, col)
        toks.append(Token(typ, loc, value))
    return toks

def usage(program_name: str):
    print(f"USAGE: {program_name} [PROGRAM_PATH] [OPTIONS] [ARGS]")
    print(f"    OPTIONS: ")
    print(f"        Empty for now")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        print("ERROR: no subcommand provided")
        exit(1)

    (program_name, args) = sys.argv
    if len(args) > 1 and isinstance(args, list):
        (program_path, options) = args
        # Parse options flags
    else:
        program_path = args

    tokens = lex_file(program_path)
    program = parse_token_as_op(tokens)
    simulate(program)
