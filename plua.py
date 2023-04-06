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
    #LBRACKET=auto()
    #RBRACKET=auto()

SEPARATORS = ['(', ')']
KEYWORDS_SIGNS = ['+']
KEYWORDS = [ str(typ).split('.')[1].lower() for typ in OpType]
KEYWORDS_BY_NAME = {
        "print": OpType.PRINT,
        "(": OpType.LPAREN,
        ")": OpType.RPAREN,
        "+": OpType.PLUS
    }
assert len(KEYWORDS_BY_NAME) == len(OpType), "Exhaustive handling of ops type in KEYWORDS_BY_NAME"
assert len(KEYWORDS_SIGNS) == len(OpType) - 3, "Exhaustive handling of keywords signs"
assert len(SEPARATORS) == len(OpType) - 2, "Exhaustive handling of SEPARATORS"

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

    if len(program) == 0:
        print("ERROR: simulating empty code")
        exit(1)

    for op in range(len(program)):
        token = program.pop(0)
        if token.typ in OpType:
            assert len(OpType) == 4, "Exhaustive handling of ops in simulate()"
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
                continue
            elif token.typ == OpType.PLUS:
                arg1 = token.value[0]
                arg2 = token.value[1]
                if arg1.typ != arg2.typ:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `+` operator can only add two arguments of the same type but found `{arg1.typ}` and `{arg2.typ}`")
                    exit(1)
                if arg1.typ == TokenType.KEYWORD:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: `+` operator can only add strings or numbers.")
                    exit(1)
                new_value = arg1.value + arg2.value
                program.append(Token(arg1.typ, arg2.loc, new_value))
            

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
                return ip
        ip += 1
    # Find a way to get token's loc
    print("ERROR: parentheses not closed, missing: ", needed)
    exit(1)

# This function checks for all tokens if it's a KEYWORD, if it is a keyword it changes that token into an op
def parse_token_as_op(tokens: List[Token]) -> Program:
    for ip, token in enumerate(tokens):
        if token.value in SEPARATORS:
            loc = token.loc
            value = parse_token_as_op(tokens[ip+1:-1])
            return Parens(loc, value)
        if token.value in KEYWORDS or token.value in KEYWORDS_SIGNS:
            typ = KEYWORDS_BY_NAME[token.value]
            assert len(OpType) == 4, "Exhaustive handling of ops in parse_token_as_op()"
            if typ == OpType.PRINT:
                if len(tokens[ip:]) == 1: 
                    print("%s:%d:%d: ERROR: expected argument but found EOF " % token.loc)
                    exit(1)
                # TODO: find a way to change this pop because it's quite slow 
                arg = tokens[ip+1]
                if arg.typ == TokenType.LPAREN:
                    closing_index = find_last_separator(tokens[ip+1:])
                    arg = parse_token_as_op(tokens[ip+1:closing_index+2])
                    for i in range(closing_index+1):
                        _ = tokens.pop(0)
                else:
                    _ = tokens.pop(ip+1)

                if isinstance(arg, Parens):
                    tokens[ip] = Op(OpType.PRINT, token.loc, arg)
                else:
                    if (arg.typ != TokenType.STR) and (arg.typ != TokenType.INT):
                        print(f"{arg.loc[0]}:{arg.loc[1]}:{arg.loc[2]}: ERROR: expected string or number but found `{arg.typ}`")
                        exit(1)
                    tokens[ip] = Op(OpType.PRINT, token.loc, arg.value)
            elif typ == OpType.PLUS:
                if tokens[0] == token:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument before the operator but found nothing.")
                    exit(1)
                if len(tokens[ip:]) == 1:
                    print(f"{token.loc[0]}:{token.loc[1]}:{token.loc[2]}: ERROR: expected one argument after the operator but found nothing.")
                    exit(1)
                tokens[ip-1] = Op(OpType.PLUS, token.loc, [tokens.pop(ip-1), tokens.pop(ip)])
    return tokens

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
