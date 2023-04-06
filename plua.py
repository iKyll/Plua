from dataclasses import dataclass
from typing import *
from enum import Enum, auto
import sys

Loc = Tuple[str, int, int]
 
class OpType(Enum):
    PRINT=auto()
    #PLUS=auto()
    #LBRACKET=auto()
    #RBRACKET=auto()

KEYWORDS = [ str(typ).split('.')[1].lower() for typ in OpType]
KEYWORDS_BY_NAME = {
        "print": OpType.PRINT
    }
assert len(KEYWORDS_BY_NAME) == len(OpType), "Exhaustive handling of ops type in KEYWORDS_BY_NAME"

@dataclass
class Op:
    typ: OpType
    loc: Loc
    value: Union[str, int]

class TokenType(Enum):
    KEYWORD=auto()
    STR=auto()
    INT=auto()

@dataclass
class Token():
    typ: TokenType
    loc: Loc
    value: Union[str, int]

Program = List[Union[Token, Op]]

def simulate(program: Program):
    for ip, op in enumerate(program):
        if op.typ in OpType:
            assert len(OpType) == 1, "Exhaustive handling of ops in simulate()"
            if op.typ == OpType.PRINT:
                value = op.value
                if isinstance(value, str):
                    print(value.encode('latin-1', 'backslashreplace').decode('unicode-escape'))
                else:
                    print(value)
                continue


# This function checks for all tokens if it's a KEYWORD, if it is a keyword it changes that token into an op
def parse_token_as_op(tokens: List[Token]) -> Program:
    for ip, token in enumerate(tokens):
        if token.value in KEYWORDS:
            typ = KEYWORDS_BY_NAME[token.value]
            assert len(OpType) == 1, "Exhaustive handling of ops in parse_token_as_op()"
            if typ == OpType.PRINT:
                if len(tokens) == 0: 
                    print("%s:%d:%d: ERROR: expected argument but found EOF " % token.loc)
                    exit(1)
                arg = tokens.pop()
                if arg.typ != TokenType.STR and arg.typ != TokenType.INT:
                    print(f"{arg.loc}: ERROR: expected string or number but found a keyword ({arg.typ})")
                    exit(1)
                tokens[ip] = Op(OpType.PRINT, token.loc, arg.value)
    return tokens

def find_token_type(value: str):
    if value in KEYWORDS:
        return TokenType.KEYWORD
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
        if line[col] == '"':
            end_word = find_index(line, col+1, space=False, quotes=True) 
            if line[end_word] != '"': assert False, "Lexer error ?"
            yield (col, TokenType.STR, line[col+1:end_word])
            col = find_index(line, end_word+1)
        else:
            end_word = find_index(line, col+1, space=False)
            value = line[col:end_word]
            yield (col, find_token_type(value), value)
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
