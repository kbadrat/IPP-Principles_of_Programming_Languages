#Vladyslav Kovalets (xkoval21)

from lib.functions import *

# Handles each argument from command line.
source, stats_file = handle_command_line()

# Handles main XML data.
root = parse_xml(source)

# Handle structure of xml. 
functions, orders_instructions_list = handle_structure(root)

# Handles each element of a sorted list with instructions.
orders_instructions_list.sort()
counter_vars, counter_insts = handle_instructions(functions, orders_instructions_list, stats_file, counter_vars, counter_insts)

# Prints statistics if needed.
if stats_file:
    stats_writes(stats_file, counter_vars, counter_insts)

sys.exit(0)
