#Vladyslav Kovalets (xkoval21)

# For input files.
source = ""
input_ = ""

# For stats.
stats_parameters = []
counter_insts = 0
counter_vars = 0

# For instructions.
for_args_no = ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"]
for_arg_var = ["DEFVAR", "POPS"]
for_arg_label = ["CALL", "LABEL", "JUMP"]
for_arg_symb = ["PUSHS", "WRITE", "EXIT", "DPRINT"]
for_args_var_symb = ["MOVE", "NOT", "INT2CHAR", "STRLEN", "TYPE"]
for_args_var_type = "READ"
for_args_var_symb_symb = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR",
                          "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR"]
for_args_label_symb_symb = ["JUMPIFEQ", "JUMPIFNEQ"]

functions = dict()  
orders_instructions_list = []  
labels_dict = dict()  
for_call_list = []

structure = dict()
structure["GF"] = dict()
structure["LF"] = None
structure["TF"] = None

# For stack.
stack_list = []
value_stack_list = []
