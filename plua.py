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
    #LBRACKET=auto()
    #RBRACKET=auto()

SEPARATORS = ['(', ')']
KEYWORDS_SIGNS = ['+', '*']
KEYWORDS = [ str(typ).split('.')[1].lower() for typ in OpType]
KEYWORDS_BY_NAME = {
        "print": OpType.PRINT,
        "(": OpType.LPAREN,
        ")": OpType.RPAREN,
        "+": OpType.PLUS,
        "*": OpType.MUL
    }
assert len(KEYWORDS_BY_NAME) == len(OpType), "Exhaustive handling of ops type in KEYWORDS_BY_NAME"
assert len(KEYWORDS_SIGNS) == len(OpType) - 3, "Exhaustive handling of keywords signs"
assert len(SEPARATORS) == len(OpType) - 3, "Exhaustive handling of SEPARATORS"

@dataclass
class Op:
    typ: OpType
    loc: Loc
    value: Union[str, int, list]

class TokenType(Enum):
    KEYWORD=auto()
    LPAREN=auto()
    RPAREN=auto()
    STR=auto()
    INT=auto()

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

Program = List[Union[Token, Op, Parens]]

def simulate(program: Program):
    in_parens = False
    if isinstance(program, Parens):
        program = program.ops
        in_parens = True
    
    ip = 0
    for op in range(len(program)):
        token = program[ip]
        if token.typ in OpType:
            assert len(OpType) == 5, "Exhaustive handling of ops in simulate()"
            if token.typ == OpType.PRINT:
                value = token.value
                if isinstance(value, Parens):
                    value = simulate(value)
                    if len(value) > 1:
                        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: too many arguments for print operator")
                        exit(1)
                    value = value[0].value
                if isinstance(value, str):
                    print(value.encode('latin-1', 'backslashreplace').decode('unicode-escape'))
                else:
                    print(value)
                program.pop(ip)
                continue
            elif token.typ == OpType.PLUS:
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                if arg2 == token: 
                    assert False, "ERROR?"
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `+` operator can only add two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ == TokenType.KEYWORD:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `+` operator can only add strings or numbers.")
                    exit(1)
                new_value = arg1.value + arg2.value
    
                ip -= 1
                program.insert(ip-3, Token(arg1.typ, arg2.loc, new_value))
            elif token.typ == OpType.MUL:
                arg1 = program.pop(ip-1)
                _    = program.pop(ip-1)
                arg2 = program.pop(ip-1)
                if arg2 == token: 
                    assert False, "ERROR?"
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `*` operator can only multiply two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ != TokenType.INT:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `*` operator can only multiply numbers.")
                    exit(1)
                new_value = arg1.value * arg2.value
    
                ip -= 1
                program.insert(ip-3, Token(arg1.typ, arg2.loc, new_value))
        elif token.typ in TokenType:
            ip += 1 

    if len(program) != 0:
        if in_parens: return program
        token = program.pop()
        print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: unhandled argument in program: `{token.value}` with type: `{token.typ}`")
        exit(1)

# Implement the brackets
def find_last_separator(program: Program) -> int:
    if len(program) == 0:
        print("ERROR: find_last_separator had an empty list")
        exit(1)
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
    print("ERROR: parentheses not closed, missing: ", needed)
    exit(1)

def parse_token_as_op(tokens: List[Token]) -> Program:
    ip = 0
    end_tokens = []
    for op in range(len(tokens)):
        if len(tokens) == 0: return end_tokens
        token = tokens[ip]
        for separator in SEPARATORS:
            if token.value == separator:
                loc = token.loc
                value = parse_token_as_op(tokens[ip+1:-1])
                return Parens(loc, value)
        if token.value in KEYWORDS or token.value in KEYWORDS_SIGNS:
            typ = KEYWORDS_BY_NAME[token.value]
            assert len(OpType) == 5, "Exhaustive handling of ops in parse_token_as_op()"
            if typ == OpType.PRINT:
                if len(tokens[ip:]) == 1:
                    print("%s:%d:%d: ERROR: expected argument but found EOF " % token.loc)
                    exit(1)
                # TODO: find a way to change this pop because it's quite slow
                arg = tokens[ip+1]
                closing_index = 0
                if arg.typ == TokenType.LPAREN:
                    closing_index = find_last_separator(tokens[ip+1:])
                    arg = parse_token_as_op(tokens[ip+1:closing_index+1])
                    if ip == 0:
                        for i in range(closing_index+1): 
                            tokens.pop(0)
                    else:
                        ip -= 1
                        for i in range(closing_index+1):
                            tokens.pop(ip-i)
                            ip -= 1
                        ip += closing_index + 1

                if isinstance(arg, Parens): end_tokens.append(Op(OpType.PRINT, token.loc, arg))
                else:
                    if (hasattr(arg, 'typ') and arg.typ != TokenType.STR) and (hasattr(arg, 'typ') and arg.typ != TokenType.INT):
                        print(f"{arg.loc[0]}:{arg.loc[1]}:{arg.loc[2]}: ERROR: expected string or number but found `{arg.typ}`")
                        exit(1)
                    end_tokens.append(Op(OpType.PRINT, token.loc, arg))
                #print(f"Pointing token is now: {tokens[ip]}, end of PRINT")
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
        elif token.typ == TokenType.STR or token.typ == TokenType.INT:
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
        except ValueError:
            print("Unknown word: ", value)
            exit(1)
        return TokenType.INT

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
            if typ == TokenType.INT:
                value = int(value)
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

    (program_name, args) = sys.argv
    if len(args) > 1 and isinstance(args, list):
        (program_path, options) = args
        # Parse options flags
    else:
        program_path = args

    tokens = lex_file(program_path)
    program = parse_token_as_op(tokens)
    simulate(program)
