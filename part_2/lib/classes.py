#Vladyslav Kovalets (xkoval21)

class Instruction:
    def __init__(self, opcode):
        self.opcode = opcode
        self.arg1 = None
        self.arg2 = None
        self.arg3 = None


class Argument:
    def __init__(self, value):
        self.val = value


class Variable:
    def __init__(self, variable_name):
        self.name = variable_name
        self.typ = None


class Stack:
    def __init__(self, stack_type, stack_value):
        self.typ = stack_type
        self.val = stack_value
        