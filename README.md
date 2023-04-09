# Plua

Plua is an programming language interpreted (At least for now). The interpreter is written in python.

## Token and Ops

An Op is defined only for the keywords.
All words in Plua are first tokens but only keywords are changed to be Ops.

## Parentheses

When an argument for a function is a paren and there are Tokens and Ops inside, the argument passed to that function is the result of the execution of the arguments inside these parens.

## Float types

All floatings numbers are automatically FLOAT types but you can cast a Interger to a Float by using the float function

### Arithmetics

In plua there are 3 Arithmetics operators: `+`, `*`, `/`
The PLUS operator (`+`) can either add two numbers of the same type or concatenate two strings.
The MUL operator (`*`) multiplies two numbers of the same type
The TRUEDIV operator (`/`) divide the first by the second. The result is always converted to an FLOAT

```
print ( 4 + 5 ) // 9
print ( 4 * 5 ) // 20
print ( 4 / 5 ) // 0.8
```


### Variables

The syntax to define a variable is:
```
def {name} : {type} => {value}
def number : int => 50
```

The syntax to reassign a variable to a new_value is 
```
{name} => {new_value}
number => 100
```
