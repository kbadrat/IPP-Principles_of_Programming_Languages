#Vladyslav Kovalets (xkoval21)

import sys
import re
import getopt
import xml.etree.ElementTree
from lib.errors import Error
from lib.classes import *
from lib.init import *


# Prints help message.
def print_help():
    print("\nThe script loads an XML representation of the program and generates output")
    print("using the input according to the command line parameters.\n")
    print("Interpreter options:\n")
    print("--help\t\t   | prints this text and helps you")
    print("--source=file\t   | input file with XML representation of the source code")
    print("--input=file\t   | input file for the interpretation of the specified source code")
    print("--stats=file\t   | file for statistics")
    print("--insts\t\t   | for number of executed instructions")
    print("--vars\t\t   | for number of initialized variables\n")

    sys.exit(0)


# Handles each argument from command line.
def handle_command_line():
    # For statistics.
    stats_file = ""
    # List of expected arguments.
    valid_args = ["help", "source=", "input=", "stats=", "insts", "vars"]

    # Get full command-line arguments.
    full_cmd_arguments = sys.argv
    # Writes all arguments except the first (file name).
    argument_list = full_cmd_arguments[1:]

    # Handles argument validation.
    try:
        arguments, values = getopt.getopt(argument_list, 'h', valid_args)
    except getopt.GetoptError:
        print("Error: Wrong option.", file=sys.stderr)
        sys.exit(Error.ERROR_SCRIPT_PARAMETER)

    # Processes each argument.
    for current_argument, current_value in arguments:
        if current_argument == '--help' or current_argument == '-h':
            print_help()

        elif current_argument == "--source":
            source = current_value

        elif current_argument == "--input":
            input_ = current_value

        elif current_argument == "--stats":
            stats_file = current_value

        elif current_argument == "--insts":
            stats_parameters.append("insts")

        elif current_argument == "--vars":
            stats_parameters.append("vars")

    # None of input and source.
    if not source and not input_:
        print("Error: None of these two arguments (input/source). At least one must be. ", file=sys.stderr)
        sys.exit(Error.ERROR_SCRIPT_PARAMETER)
    # Missing data is read from standard input.
    elif not source:
        source = sys.stdin
    # elif not input_:
    #   input_ = sys.stdin

    # There is no file where to write statistics
    if stats_parameters and not stats_file:
        print("Error: No file for statistics.", file=sys.stderr)
        sys.exit(Error.ERROR_SCRIPT_PARAMETER)

    return source, stats_file


# Handles main XML data.
def parse_xml(source):
    try:
        # Root has a tag and a dictionary of attributes.
        root = xml.etree.ElementTree.parse(source).getroot()
    except:
        print("Error: Wrong XML format.", file=sys.stderr)
        sys.exit(Error.ERROR_XML_FORMAT)
    # Checks root tag.
    if root.tag != "program":
        print("Error: Wrong root tag.", file=sys.stderr)
        sys.exit(Error.ERROR_XML_STRUCTURE)
    # Checks all attributes.
    for attribute in root.attrib:
        if attribute not in ['language', 'name', 'description']:
            print("Error: Wrong XML attribute.", file=sys.stderr)
            sys.exit(Error.ERROR_XML_STRUCTURE)
    # Checks name of language.
    if root.attrib["language"].upper() != "IPPCODE22":
        print("Error: Wrong attribute language.", file=sys.stderr)
        sys.exit(Error.ERROR_XML_STRUCTURE)

    return root


# Handle structure of xml. 
def handle_structure(root):
    orders_instructions_list = []
    functions = dict()
    for root in root:
        # Checks if the name of instruction is written correctly.
        if root.tag != "instruction":
            print("Error: Wrong name of instruction.", file=sys.stderr)
            sys.exit(Error.ERROR_XML_STRUCTURE)

        # Checks if the instruction is written correctly with order and opcode.
        if 'order' not in root.attrib or 'opcode' not in root.attrib:
            print("Error: No order or opcode.", file=sys.stderr)
            sys.exit(Error.ERROR_XML_STRUCTURE)

        # Writes the order number and checks.
        try:
            order = int(root.attrib["order"])
            if order <= 0:
                print("Error: Wrong(negative/zero) number of order.")
                sys.exit(Error.ERROR_XML_STRUCTURE)
        except:
            print("Error: Order isn't number.")
            sys.exit(Error.ERROR_XML_STRUCTURE)

        # Checks the uniqueness of the order.
        if order in orders_instructions_list:
            print("Error: Order number repeats.", file=sys.stderr)
            sys.exit(Error.ERROR_XML_STRUCTURE)
        else:
            orders_instructions_list.append(order)

        # Preparing for opcode control. Filling the dictionary with instructions.
        opcode = root.attrib["opcode"].upper()
        functions[order] = Instruction(opcode)

        # No args.
        if opcode in for_args_no:
            pass
        # Var.
        elif opcode in for_arg_var:
            handle_xml(root, 1, ["var"])
            arg_var(root, order, functions)
        # Label.
        elif opcode in for_arg_label:
            handle_xml(root, 1, ["label"])
            arg_label(root, order, opcode, functions)
        # Symb.
        elif opcode in for_arg_symb:
            handle_xml(root, 1, ["symb"])
            arg_symb(root, order, functions)
        # Var, symb.
        elif opcode in for_args_var_symb:
            arg_order = handle_xml(root, 2, ["var", "symb"])
            args_two(root, order, arg_order, functions)
        # Var, type.
        elif opcode == for_args_var_type:
            arg_order = handle_xml(root, 2, ["var", "type"])
            args_var_type(root, order, arg_order, functions)
        # Var, symb, symb.
        elif opcode in for_args_var_symb_symb:
            arg_order = handle_xml(root, 3, ["var", "symb", "symb"])
            args_three(root, order, arg_order, functions)
        # Label, symb, symb.
        elif opcode in for_args_label_symb_symb:
            arg_order = handle_xml(root, 3, ["label", "symb", "symb"])
            args_three(root, order, arg_order, functions)
        else:
            print("Error: Wrong operator.", file=sys.stderr)
            sys.exit(Error.ERROR_XML_STRUCTURE)


    return functions, orders_instructions_list


# Checks for the existence of a frame and a variable.
def check_frame_splitted_arg(variable_name, frame, structure):
    if structure[frame] is None:
        print("Error: No frame.", file=sys.stderr)
        sys.exit(Error.ERROR_WRONG_FRAME)
    elif variable_name in structure[frame] is False:
        print("Error: No varialbe in frame.", file=sys.stderr)
        sys.exit(Error.ERROR_WRONG_VARIABLE)


# Works with escape sequence.
def handle_sequence(sequence_string):
    # Create list with escape sequences.
    sequence_list = re.findall('(\\\\[0-9]{3})', sequence_string)
    # Until the list ends.
    while sequence_list:
        # The first element from the list is processed and then removed from the list.
        sequence = sequence_list[0]
        sequence_string = sequence_string.replace(sequence, chr(int(sequence[1:])))
        sequence_list.remove(sequence)

    return sequence_string


# Handles the argument and its type.
def arg_type_value(structure, typ, argument):
    if argument.type == "var":
        variable = argument.val.split('@')
        check_frame_splitted_arg(variable[1], variable[0], structure)
        val = structure[variable[0]][variable[1]].val

        # To get argument and its type.
        if not typ:
            typ = structure[variable[0]][variable[1]].typ
            return typ, val
        # To get only argument.
        return val
    else:
        # To get only argument.
        if typ:
            if argument.type != typ:
                print("Error: Wrong type.", file=sys.stderr)
                sys.exit(Error.ERROR_OPERAND_TYPE)
            return argument.val
        # To get argument and its type.
        return argument.type, argument.val


# Writes statistics to a file.
def stats_writes(stats_file, counter_vars, counter_insts):
    # Opens a file for writing.
    try:
        opened_file = open(stats_file, "w")
    except:
        print("Error: Can't open file for statistics.", file=sys.stderr)
        sys.exit(Error.ERROR_OUTPUT)

    # Outputs to the file what was requested.
    for word in stats_parameters:
        if word == "vars":
            print(counter_vars, file=opened_file)
        elif word == "insts":
            print(counter_insts, file=opened_file)

    opened_file.close()


# Works with xml arguments.
def handle_xml(args, args_num, is_type):

    # Checks number of arguments.
    if args_num != len(args):
        print("Error: Wrong number of arguments.", file=sys.stderr)
        sys.exit(Error.ERROR_XML_STRUCTURE)
    else:
        tags_list = []
        for num in range(1, args_num + 1):
            tags_list.append("arg" + str(num))

    # Handles arguments.
    arg_order = []
    for arg in args:
        # Checks tag of argument.
        if arg.tag not in tags_list:
            print("Error: Wrong tag.", file=sys.stderr)
            sys.exit(Error.ERROR_XML_STRUCTURE)

        arg_order.append(arg.tag)
        check = is_type[int(arg.tag[3]) - 1]

        # Checks the type and value.
        if check == "symb":
            if arg.attrib["type"] == "var":
                if arg.text is None:
                    print("Error: No name of variable.", file=sys.stderr)
                    sys.exit(Error.ERROR_XML_STRUCTURE)

                # Checks the correctness of a variable name.
                if not re.match(r'^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$', arg.text):
                    print("Error: Wrong name of variable.", file=sys.stderr)
                    sys.exit(Error.ERROR_XML_STRUCTURE)

            elif arg.attrib["type"] == "int":
                # Checks the correctness of int.
                if not re.match(r'^[+-]?[\d]+$', arg.text):
                    print("Error: Misuse of int.", file=sys.stderr)
                    sys.exit(Error.ERROR_XML_STRUCTURE)

            elif arg.attrib["type"] == "bool":
                # Checks the correctness of bool.
                if not re.match(r'^true$|^false$', arg.text):
                    print("Error: Misuse of bool.", file=sys.stderr)
                    sys.exit(Error.ERROR_XML_STRUCTURE)

            elif arg.attrib["type"] == "string":
                # If no string, then it is empty.
                if arg.text is None:
                    arg.text = ""

                # Checks the correctness of string.
                if not re.match(r'^([^\s\\#]|(\\\d{3}))*$', arg.text):
                    print("Error: Misuse of string.", file=sys.stderr)
                    sys.exit(Error.ERROR_XML_STRUCTURE)

            elif arg.attrib["type"] == "nil":
                # Checks the correctness of nil.
                if arg.text != "nil":
                    print("Error: Misuse of nil.", file=sys.stderr)
                    sys.exit(Error.ERROR_XML_STRUCTURE)
            else:
                print("Error: Wrong type.", file=sys.stderr)
                sys.exit(Error.ERROR_XML_STRUCTURE)

        elif check == "var":
            if arg.text is None:
                print("Error: No name of variable.", file=sys.stderr)
                sys.exit(Error.ERROR_XML_STRUCTURE)
            # Checks the correctness of a variable name.
            if re.match(r'^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$', arg.text) is None:
                print("Error: Wrong name of variable.", file=sys.stderr)
                sys.exit(Error.ERROR_XML_STRUCTURE)  

        elif check == "type":
            # Checks the correctness of a type.
            if not re.match(r'int$|^bool$|^string$|^nil$', arg.text):
                print("Error: Misuse of type.", file=sys.stderr)
                sys.exit(Error.ERROR_XML_STRUCTURE)

        elif check == "label":
            # Checks the correctness of a label name.
            if not re.match(r'(?i)^[a-z_\-$&%*!?][a-z_\-$&%*!?0-9]*$', arg.text):
                print("Error: Misuse of label.", file=sys.stderr)
                sys.exit(Error.ERROR_XML_STRUCTURE)

    return arg_order


# To work with arguments.
# Var.
def arg_var(root, order, functions):
    functions[order].arg1 = Argument(root[0].text)


# Label.
def arg_label(root, order, opcode, functions):
    functions[order].arg1 = Argument(root[0].text)

    # Save the label and checks for uniqueness
    if opcode == "LABEL":
        label = root[0].text

        if label in labels_dict:
            print("Error: Labels must be unique.", file=sys.stderr)
            sys.exit(Error.ERROR_SEMANTIC)

        labels_dict[label] = order


# String.
def arg_symb(root, order, functions):
    if root[0].attrib["type"] == "string" and root[0].text is None:
        functions[order].arg1 = Argument("")
    else:
        functions[order].arg1 = Argument(root[0].text)

    functions[order].arg1.type = root[0].attrib["type"]


# For var and type.
def args_var_type(root, order, arg_order, functions):
    functions[order].arg1 = Argument(root[arg_order.index("arg1")].text)
    functions[order].arg2 = Argument(root[arg_order.index("arg2")].text)


# For two args.
def args_two(root, order, arg_order, functions):
    functions[order].arg1 = Argument(root[arg_order.index("arg1")].text)

    if root[arg_order.index("arg2")].attrib["type"] == "string" and root[arg_order.index("arg2")].text is None:
        functions[order].arg2 = Argument("")
    else:
        functions[order].arg2 = Argument(root[arg_order.index("arg2")].text)

    functions[order].arg2.type = root[arg_order.index("arg2")].attrib["type"]


# For three args.
def args_three(root, order, arg_order, functions):
    args_two(root, order, arg_order, functions)
    if root[arg_order.index("arg3")].attrib["type"] == "string" and root[arg_order.index("arg3")].text is None:
        functions[order].arg3 = Argument("")
    else:
        functions[order].arg3 = Argument(root[arg_order.index("arg3")].text)

    functions[order].arg3.type = root[arg_order.index("arg3")].attrib["type"]


# Handles each element of a sorted list with instructions.
def handle_instructions(functions, orders_instructions_list, stats_file, counter_vars, counter_insts):
    i = 0
    while i < len(orders_instructions_list):

        # Gets the name of the instruction from the dictionary.
        instruction = functions[orders_instructions_list[i]]

        # Separates each element by "@".
        try:
            splitted_arg = instruction.arg1.val.split('@')
        except:
            splitted_arg = ""

        # Checks separately the name of the instruction.
        instruction_name = functions[orders_instructions_list[i]].opcode

        # Copy ⟨symb⟩ value to ⟨var⟩.
        if instruction_name == "MOVE":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            typ, val = arg_type_value(structure, None, instruction.arg2)
            structure[splitted_arg[0]][splitted_arg[1]].typ = typ
            structure[splitted_arg[0]][splitted_arg[1]].val = val

        # Creates a new temporary frame.
        elif instruction_name == "CREATEFRAME":
            structure["TF"] = dict()

        # The temporary frame becomes the local frame.
        elif instruction_name == "PUSHFRAME":
            # Access to an undefined frame.
            if structure["TF"] is None:
                print("Error: Wrong temporary frame.", file=sys.stderr)
                sys.exit(Error.ERROR_WRONG_FRAME)

            # The frame will be available via LF and will overlay the original frames.
            stack_list.append(structure["TF"])
            structure["LF"] = structure["TF"]
            structure["TF"] = None

        # Move the top LF frame from the frame stack to the TF.
        elif instruction_name == "POPFRAME":
            # If no frame is available in the LF.
            if structure["LF"] is None:
                print("Error: Wrong local frame.", file=sys.stderr)
                sys.exit(Error.ERROR_WRONG_FRAME)

            structure["TF"] = structure["LF"]
            # Removes the top from the stack.
            stack_list.pop(-1)

            if stack_list:
                # Removes and returns the top from the stack.
                structure["LF"] = stack_list.pop(-1)
                # Adds LF to top stack.
                stack_list.append(structure["LF"])
        # Defines a variable within a specified frame.
        elif instruction_name == "DEFVAR":
            # Checks if the frame exists. 
            if structure[splitted_arg[0]] is None:
                print("Error: No frame.", file=sys.stderr)
                sys.exit(Error.ERROR_WRONG_FRAME)

            # For stats.
            if stats_file:
                counter_vars += 1

            # Defines.
            structure[splitted_arg[0]][splitted_arg[1]] = Variable(splitted_arg[1])
        # Saves the current position and executes jump to the specified label.
        elif instruction_name == "CALL":
            # Adds current position.
            for_call_list.append(i)
            i = orders_instructions_list.index(labels_dict[instruction.arg1.val]) - 1
        # Removes and returns last element from the call list.
        elif instruction_name == "RETURN":
            i = for_call_list.pop(-1)
        # Saves the value to the data stack.
        elif instruction_name == "PUSHS":
            # Check if type is var.
            if instruction.arg1.type == "var":
                check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)
                # Saves the value.
                value_stack_list.append(Stack(structure[splitted_arg[0]][splitted_arg[1]].typ, structure[splitted_arg[0]][splitted_arg[1]].val))
            else:
                # Saves the value
                value_stack_list.append(Stack(instruction.arg1.type, instruction.arg1.val))
        # Extracts the value and stores it in a variable.
        elif instruction_name == "POPS":
            # If the stack is empty.
            if not value_stack_list:
                print("Error: Stack is empty.", file=sys.stderr)
                sys.exit(Error.ERROR_NO_VALUE)
            else:
                check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Removes and returns the top value from the stack.
            popped = value_stack_list.pop(-1)
            structure[splitted_arg[0]][splitted_arg[1]].typ = popped.typ
            structure[splitted_arg[0]][splitted_arg[1]].val = popped.val
        # Mathematical operations.
        elif instruction_name == "ADD" or instruction_name == "SUB" or instruction_name == "MUL" or instruction_name == "IDIV":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            try:
                a = int(arg_type_value(structure, "int", instruction.arg2))
                b = int(arg_type_value(structure, "int", instruction.arg3))
            except:
                print("Error: Value for mathematical operations isn't integer.", file=sys.stderr)
                sys.exit(Error.ERROR_OPERAND_TYPE)

            structure[splitted_arg[0]][splitted_arg[1]].typ = "int"

            # Saves the result to variables.
            if instruction_name == "ADD":
                res = a + b
            elif instruction_name == "SUB":
                res = a - b
            elif instruction_name == "MUL":
                res = a * b
            elif instruction_name == "IDIV":
                if b == 0:
                    print("Error: Can't divide by zero.", file=sys.stderr)
                    sys.exit(Error.ERROR_WRONG_OPERAND_VALUE)
                res = a // b

            structure[splitted_arg[0]][splitted_arg[1]].val = res
        # Evaluates the relational operator.
        elif instruction_name == "LT" or instruction_name == "GT":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets typ and its arguments.
            typ, value = arg_type_value(structure, None, instruction.arg2)
            value2 = arg_type_value(structure, typ, instruction.arg3)

            # Type is bool.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "bool"

            # Variables for comparison.
            if typ == "int":
                value = int(value)
                value2 = int(value2)
            # False if invalid or true if valid.
            if instruction_name == "LT" and value < value2:
                structure[splitted_arg[0]][splitted_arg[1]].val = "true"
            elif instruction_name == "GT" and value > value2:
                structure[splitted_arg[0]][splitted_arg[1]].val = "true"
            else:
                structure[splitted_arg[0]][splitted_arg[1]].val = "false"

        # Evaluates the relational operator.
        elif instruction_name == "EQ":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets typ and its arguments.
            typ, value = arg_type_value(structure, None, instruction.arg2)
            typ2, value2 = arg_type_value(structure, None, instruction.arg3)

            # Type is bool - false.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "bool"
            structure[splitted_arg[0]][splitted_arg[1]].val = "false"

            # Variables for comparison.
            if typ == typ2:
                if typ == "int":
                    value = int(value)
                    value2 = int(value2)
                # True if valid.
                if value == value2:
                    structure[splitted_arg[0]][splitted_arg[1]].val = "true"
            # For nil operand.
            elif typ != "nil" and typ2 != "nil":
                print("Error: Misuse of type.", file=sys.stderr)
                sys.exit(Error.ERROR_OPERAND_TYPE)

        # Applies conjunction or disjunction to operands.
        elif instruction_name == "AND" or instruction_name == "OR":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets arguments of bool type.
            value = arg_type_value(structure, "bool", instruction.arg2)
            value2 = arg_type_value(structure, "bool", instruction.arg3)


            # Applies conjunction or disjunction and writes the result.
            if (value == "true" and value2 == "true") or (value == "true" or value2 == "true"):
                structure[splitted_arg[0]][splitted_arg[1]].val = "true"
            else:
                structure[splitted_arg[0]][splitted_arg[1]].val = "false"
        # Negation to the bool value.
        elif instruction_name == "NOT":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets argument of bool type.
            value = arg_type_value(structure, "bool", instruction.arg2)
            # Type is bool.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "bool"

            # Negation.
            if value == "true":
                value = "false"
            else:
                value = "true"

            # Writes the result.
            structure[splitted_arg[0]][splitted_arg[1]].val = value

        # According to Unicode, a numeric value is converted to a character that forms a one-character string.
        elif instruction_name == "INT2CHAR":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets argument of int type.
            value = int(arg_type_value(structure, "int", instruction.arg2))
            # Type is string.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "string"

            # Converts.
            try:
                structure[splitted_arg[0]][splitted_arg[1]].val = chr(value)
            # If the ordinal value of the character is not valid in Unicode.
            except:
                print("Error: Wrong value of a character in Unicode.", file=sys.stderr)
                sys.exit(Error.ERROR_STRING)

        # Saves the ordinal value of a character (according to Unicode).
        elif instruction_name == "STRI2INT" or instruction_name == "GETCHAR":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets arguments of string and int types.
            value = handle_sequence(arg_type_value(structure, "string", instruction.arg2))
            value2 = int(arg_type_value(structure, "int", instruction.arg3))

            # Checks indexing.
            if value2 < 0 or value2 >= len(value):
                print("Error: Wrong index.", file=sys.stderr)
                sys.exit(Error.ERROR_STRING)

            # Saves the ordinal value of a character to a specific position.
            if instruction_name == "STRI2INT":
                # Type is integer.
                structure[splitted_arg[0]][splitted_arg[1]].typ = "int"
                structure[splitted_arg[0]][splitted_arg[1]].val = ord(value[value2])
            else:
                # Type is string.
                structure[splitted_arg[0]][splitted_arg[1]].typ = "string"
                # Saves a character to a specific position.
                structure[splitted_arg[0]][splitted_arg[1]].val = value[value2]

        # Read the value according to the specified type and store it in a variable.
        elif instruction_name == "READ":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Retrieves one value.
            try:
                value = input()
            # In case of incorrect or missing input, the val is nil.
            except:
                instruction.arg2.val = "nil"
                value = "nil"

            # Converts to the specified type.
            if instruction.arg2.val == "int":
                value = int(value)
            elif instruction.arg2.val == "string":
                value = str(value)
            elif instruction.arg2.val == "bool":
                if value.lower() == "true":
                    pass
                else:
                    value = "false"
            else:
                instruction.arg2.val = "nil"
                value = "nil"

            structure[splitted_arg[0]][splitted_arg[1]].val = value
            structure[splitted_arg[0]][splitted_arg[1]].typ = instruction.arg2.val

        # Prints the value to standard output.
        elif instruction_name == "WRITE":
            # Check if type is var.
            if instruction.arg1.type == "var":
                check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

                # Gets typy and its value.
                typ = structure[splitted_arg[0]][splitted_arg[1]].typ
                value = structure[splitted_arg[0]][splitted_arg[1]].val
            else:
                # Gets typy and its value.
                typ = instruction.arg1.type
                value = instruction.arg1.val

            if typ == "int":
                print(int(value), end='')
            elif typ == "bool":
                print(value, end='')
            elif typ == "string":
                print(handle_sequence(value), end='')
            else:
                # The value of nil is an empty string.
                print("", end='')
        # Saves the string created by the concatenation of two string operands.
        elif instruction_name == "CONCAT":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets arguments of string type.
            value = arg_type_value(structure, "string", instruction.arg2)
            value2 = arg_type_value(structure, "string", instruction.arg3)

            # Type is string.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "string"
            # Saves the concatenated string.
            structure[splitted_arg[0]][splitted_arg[1]].val = value + value2
        # Finds the number of characters and this length is stored as an integer.
        elif instruction_name == "STRLEN":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Gets argument of string type.
            value = arg_type_value(structure, "string", instruction.arg2)

            # Type is integer.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "int"

            # Saves the length as an integer.
            structure[splitted_arg[0]][splitted_arg[1]].val = len(handle_sequence(value))

        # Changes the character to a specific position in the string.
        elif instruction_name == "SETCHAR":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Checks for correct type.
            if structure[splitted_arg[0]][splitted_arg[1]].typ != "string":
                print("Error: Type isn't string. (setchar)", file=sys.stderr)
                sys.exit(Error.ERROR_OPERAND_TYPE)

            # Gets arguments of integer and string types.
            value = int(arg_type_value(structure, "int", instruction.arg2))
            value2 = handle_sequence(arg_type_value(structure, "string", instruction.arg2))

            # Handle sequence.
            sequence_string = handle_sequence(structure[splitted_arg[0]][splitted_arg[1]].val)

            # Checks out-of-string indexing.
            if value >= len(sequence_string) or value < 0:
                print("Error: Wrong index.", file=sys.stderr)
                sys.exit(Error.ERROR_STRING)

            # Checks if a string is empty.
            if not value2:
                print("Error: No string for replace", file=sys.stderr)
                sys.exit(Error.ERROR_STRING)
            else:
                sequence_string[value] = value2[0]

            # Saves modified sequence.
            structure[splitted_arg[0]][splitted_arg[1]].val = sequence_string

        # Detects the symbol type.
        elif instruction_name == "TYPE":
            check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

            # Type is string.
            structure[splitted_arg[0]][splitted_arg[1]].typ = "string"

            # Checks if type is var.
            if instruction.arg2.type == "var":
                # Separates second argument by "@".
                splitted_arg2 = instruction.arg2.val.split('@')
                check_frame_splitted_arg(splitted_arg2[1], splitted_arg2[0], structure)

                # If the variable is uninitialized, then type is empty string
                if structure[splitted_arg2[0]][splitted_arg2[1]].typ is None:
                    value = ""
                else:
                    value = structure[splitted_arg2[0]][splitted_arg2[1]].typ
            else:
                value = instruction.arg2.type

            # Saves a string indicating this type.
            structure[splitted_arg[0]][splitted_arg[1]].val = value

        # Special instructions indicating by labels.
        elif instruction_name == "LABEL":
            pass

        # Jumps to the specified label.
        elif instruction_name == "JUMP":
            # Checks if there are label to jump.
            if instruction.arg1.val not in labels_dict:
                print("Error: No label to jump", file=sys.stderr)
                sys.exit(Error.ERROR_SEMANTIC)

            # Jump.
            i = orders_instructions_list.index(labels_dict[instruction.arg1.val]) - 1

        # Jumps to the specified label depending on the conditions.
        elif instruction_name == "JUMPIFEQ" or instruction_name == "JUMPIFNEQ":
            # Gets typ and its arguments.
            typ, value = arg_type_value(structure, None, instruction.arg2)
            typ2, value2 = arg_type_value(structure, None, instruction.arg3)

            # If the variables are of the same type.
            if typ == typ2:
                if typ == "int":
                    value = int(value)
                    value2 = int(value2)
                # If the values are equal.
                if instruction_name == "JUMPIFEQ" and value == value2:
                    i = orders_instructions_list.index(labels_dict[instruction.arg1.val]) - 1
                # If the values are not equal.
                elif instruction_name == "JUMPIFNEQ" and value != value2:
                    i = orders_instructions_list.index(labels_dict[instruction.arg1.val]) - 1
            # If both types are not "nil" and equal.
            elif typ != "nil" and typ2 != "nil":
                print("Error: Wrong type. (JUMPIFEQ/JUMPIFNEQ).", file=sys.stderr)
                sys.exit(Error.ERROR_OPERAND_TYPE)
            else:
                i = orders_instructions_list.index(labels_dict[instruction.arg1.val]) - 1

        # Terminates program execution, prints statistics if needed, and exits interpreter with return code.
        elif instruction_name == "EXIT":
            # Check if type is var.
            if instruction.arg1.type == "var":
                check_frame_splitted_arg(splitted_arg[1], splitted_arg[0], structure)

                # Saves return code.
                value = int(structure[splitted_arg[0]][splitted_arg[1]].val)
            else:
                # Saves return code.
                value = int(instruction.arg1.val)

            # Checks if a return code is invalid
            if value < 0 or 49 < value:
                print("Error: Wrong return code.", file=sys.stderr)
                sys.exit(Error.ERROR_WRONG_OPERAND_VALUE)

            # Prints statistics if needed.
            if stats_file:
                stats_writes(stats_file, counter_vars, counter_insts + 1)

            # Terminates program.
            sys.exit(value)

        elif instruction_name == "BREAK":
            # Prints the state of the interpreter stderr at a given time.
            # (position in the code, the content of the frames, the number of executed instructions)
            pass

        elif instruction_name == "DPRINT":
            # Prints the specified value to stderr.
            pass

        # Counts instructions if needed.
        if stats_file:
            counter_insts += 1

        # Next instruction.
        i += 1

    return counter_vars, counter_insts
