<?php
//Vladyslav Kovalets (xkoval21)
ini_set('display_errors', 'stderr');

//For errors.
define("ERROR_SCRIPT_PARAMETER", 10);
define("ERROR_OUTPUT", 12);
define("ERROR_HEAD", 21);
define("ERROR_OPCODE", 22);
define("ERROR_LEXICAL_OR_SYNTEX", 23);

//For statistics.
class Counters
{
    public $stats_arr = array();
    public $instructions = 0;
    public $comments = 0;
    public $label = 0;
    public $labels = array();
    public $jumps = 0;
}

$if_stats = false;
$if_header = false;
$counters = new Counters();

//For the name of the file to which the statistics will be written.
$file = '';

//Handling program launch arguments.
handle_arguments($argc, $argv, $if_stats, $counters, $file);

//Handling stdin. Takes data from stdin and removes unnecessary characters.
handle_stdin($counters, $if_header);

//Writing statistics to a file.
print_stats($if_stats, $counters, $file);

//Printing XML.
echo $xml->saveXML();

/////////////////////////////FUNCTIONS/////////////////////////////

//Handling program launch arguments.
function handle_arguments($argc, $argv, $if_stats, $counters, $file)
{
    global $if_stats;
    global $file;

    for ($i = 1; $i < $argc; $i++) 
    {
        if($argv[$i] == "--help" )
        {
            if($argc > 2)
            {
                error_log("Wrong combination of parameters! Use \"--help\" for help.\n");
                exit(ERROR_SCRIPT_PARAMETER);
            }
            echo ("The script reads the source code in IPPcode22 from input, checks the lexical and syntactic correctness "); 
            echo ("of the code, and writes a representation of the program to standard XML output.\n\n");
            echo ("Usage: parse.php [options] <inputFile\n");
            echo ("--help       - Prints help. No other arguments accepted with these option.\n");
            echo ("--stats=file - Sets the file that the statistics will be written to.\n");
            echo ("\nThese parameters use only with --stats.\n");
            echo ("--loc        - Count lines where occurs instructions in the code.\n");
            echo ("--comments   - Count number of comments.\n");
            echo ("--labels     - Count uniqe labels.\n");
            echo ("--jumps      - Count instructions which provides jump in the program.\n");
            exit(0);
        }
        //Checks statistics arguments.
        if(preg_match('/^(--stats)=([^="]*)$/', $argv[$i]))
        {
            $if_stats = true;
            $file = preg_replace('/^(--stats)=/', "", $argv[$i]);
        }
        //If there are matches, it adds to the end of the array to keep the sequence.
        elseif($argv[$i] == '--loc')
            $counters->stats_arr[] = 'loc'; 

        elseif($argv[$i] == '--comments')
            $counters->stats_arr[] = 'comments'; 

        elseif($argv[$i] == '--labels')
            $counters->stats_arr[] = 'labels'; 

        elseif($argv[$i] == '--jumps')
            $counters->stats_arr[] = 'jumps'; 

        else
        {
            error_log("Wrong parameter.\n");
            exit(ERROR_SCRIPT_PARAMETER);
        }   
    }
}

//Handling stdin. Takes data from stdin and removes unnecessary characters.
function handle_stdin($counters, $if_header)
{
    global $xml, $xml_node;
    //The loop takes data from stdin and removes unnecessary characters.
    while($line = fgets(STDIN))
    {
        //Removes one type of comment.
        if(preg_match('/#.*/', $line))
        {
            $line = preg_replace('/#.*/', "", $line);
            //Raises counter for comment statistics.
            $counters->comments++;
        }

        //Removes comment line.
        if (preg_match('/#/', $line))
        {
            //Raises counter for comment statistics.
            $counters->comments++;
            //Move on to the next line.
            continue;
        }            
        //Removes tabs, line breaks, and space sequencing.
        $line = trim(preg_replace('/\s\s+/', ' ', $line));

        //If the line is empty, then take the next line.
        if ($line == '')
            continue;

        //Checks header of IPPcode22.
        if($if_header == false)
        {
            if (strtoupper($line) == ".IPPCODE22")
            {    
                //Creates DOMDocument and settings it. For xml.
                $xml = new DOMDocument('1.0', "UTF-8");           //xml version="1.0" encoding="UTF-8"
                $xml->formatOutput = true;                        //Structures the output.
                $xml_node = $xml->createElement('program');       //<program language   Nastaveni korene XML stromu.
                $xml->appendChild($xml_node); 
                $xml_node->setAttribute("language", "IPPcode22"); //<program language="IPPcode22">
                //Header of IPPcode22 is ready! 
                $if_header = true;
                continue;
            }
            else 
            {
                error_log("Chybna ci chybejici hlavicka ve zdrojovem kodu!\n");
                exit(ERROR_HEAD);
            }
        }

        //Raises counter for instruction statistics.
        $counters->instructions++;

        //Divides into lexical tokens.
        $splitted = explode(' ',$line);

        handle_instructions($splitted, $counters);    
    }
}

//Handling instructions(functions).
function handle_instructions($splitted, $counters)
{
    //Сonvert all letters of a token to uppercase.
    $splitted[0] = strtoupper($splitted[0]);
    //All instructions are sorted.
    switch($splitted[0])
    {
        case "CREATEFRAME":
        case "PUSHFRAME":
        case "POPFRAME":
        case "RETURN":
        case "BREAK":
            creteframe_pushframe_popframe_return_break($splitted, $counters);
            break;

        case "DEFVAR":
        case "POPS":
            defvar_pops($splitted, $counters);
            break;

        case "CALL":
        case "LABEL":
        case "JUMP":
            call_label_jump($splitted, $counters);
            break;
 
        case "PUSHS":
        case "WRITE":
        case "EXIT":
        case "DPRINT":
            pushs_write_exit_dprint($splitted, $counters);
            break;

        case "MOVE":
        case "NOT":
        case "INT2CHAR":
        case "STRLEN":
        case "TYPE":
            move_not_int2char_strlen_type($splitted, $counters);
            break;

        case "READ":
            read($splitted, $counters);
            break;

        case "ADD":
        case "SUB":
        case "MUL":
        case "IDIV":
        case "LT":
        case "GT":
        case "EQ":
        case "AND":
        case "OR":
        case "STR2INT":
        case "CONCAT":
        case "GETCHAR":
        case "SETCHAR":
            add_sub_mul_idiv_lt_gt_eq_and_or_str2int_concat_getchar_setchar($splitted, $counters);
            break;

        case "JUMPIFEQ":
        case "JUMPIFNEQ":
            jumpifeq_jumpifneq($splitted, $counters);
            break;
        //Others.
        default:
            error_log("Wrong function \"$splitted[0]\".\n");
            exit(ERROR_OPCODE);
    }
}

//Works with functions without arguments. 
function creteframe_pushframe_popframe_return_break($splitted, $counters)
{
    if(count($splitted) != 1)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }

    //Raises counter for jump statistics.
    if($splitted[0] == "RETURN")
        $counters->jumps++; 

    create_xml_functions($counters->instructions, $splitted[0]);
}

//Works with functions with 1(symb) argument. 
function pushs_write_exit_dprint($splitted, $counters)
{
    if(count($splitted) != 2)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif(is_type($splitted[1]) == true)
        create_xml_arguments(create_xml_functions($counters->instructions, $splitted[0]), 1, htmlspecialchars(is_constant($splitted[1])), is_type($splitted[1]));
    else
    {
        error_log("Wrong format \"$splitted[1]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
}

//Works with functions with 1(var) argument. 
function defvar_pops($splitted, $counters)
{
    if(count($splitted) != 2)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif(is_variable($splitted[1]) == true)
        create_xml_arguments(create_xml_functions($counters->instructions, $splitted[0]), 1,htmlspecialchars($splitted[1]), "var");
    else
    {
        error_log("Wrong format \"$splitted[1]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
}

//Works with functions with 1(label) argument. 
function call_label_jump($splitted, $counters)
{
    if(count($splitted) != 2)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif(is_label($splitted[1]))
    {
        create_xml_arguments(create_xml_functions($counters->instructions, $splitted[0]), 1, htmlspecialchars($splitted[1]), "label");

        //Raises counter for jump statistics.
        if($splitted[0] == "CALL" || $splitted[0] == "JUMP")
            $counters->jumps++;
        //Raises counter for labels statistics.
        elseif(($splitted[0] == "LABEL") && (array_key_exists($splitted[1],$counters->labels) == false))
        {
            $counters->labels[] = $splitted[1]; //Add label to array with labels;
            $counters->label++;
        }
    }
    else
    {
        error_log("Wrong format \"$splitted[1]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
}

//Works with functions with 2(var, symb) arguments. 
function move_not_int2char_strlen_type($splitted, $counters)
{
    if(count($splitted) != 3)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif((is_variable($splitted[1])) && ($type = is_type($splitted[2])))
    {
        $add_params = params($counters, $splitted[0]);
        
        create_xml_arguments($add_params, 1, htmlspecialchars($splitted[1]), 'var');
        create_xml_arguments($add_params, 2, htmlspecialchars(is_constant($splitted[2])), $type);
    }
    else
    {
        error_log("Wrong format \"$splitted[1]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }    
}

//Works with function with 2(var, type) arguments. 
function read($splitted, $counters)
{
    if(count($splitted) != 3)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif((is_variable($splitted[1])) && (is_constant($splitted[2])))
    {
        $add_params = params($counters, $splitted[0]);

        create_xml_arguments($add_params, 1, htmlspecialchars($splitted[1]), 'var');
        create_xml_arguments($add_params, 2, $splitted[2], 'type');
    }
    else
    {
        error_log("Wrong format \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
}

//Works with functions with 3(var, symb1, symb2) arguments. 
function add_sub_mul_idiv_lt_gt_eq_and_or_str2int_concat_getchar_setchar($splitted, $counters)
{
    if(count($splitted) != 4)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif((is_variable($splitted[1])) && ($type1 = is_type($splitted[2])) && ($type2 = is_type($splitted[3])))
    {
        $add_params = params($counters, $splitted[0]);

        create_xml_arguments($add_params, 1,  htmlspecialchars($splitted[1]), 'var');
        create_xml_arguments($add_params, 2,  htmlspecialchars(is_constant($splitted[2])), $type1);
        create_xml_arguments($add_params, 3,  htmlspecialchars(is_constant($splitted[3])), $type2);
    }
    else
    {
        error_log("Wrong format \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
}

//Works with functions with 3(label, symb1, symb2) arguments.    
function jumpifeq_jumpifneq($splitted, $counters)
{
    if(count($splitted) != 4)
    {
        error_log("Incorrect use of a function \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
    elseif((is_label($splitted[1])) && ($type1 = is_type($splitted[2])) && ($type2 = is_type($splitted[3])))
    {
        $counters->jumps;
        $add_params = params($counters, $splitted[0]);

        create_xml_arguments($add_params, 1, htmlspecialchars($splitted[1]), 'label');
        create_xml_arguments($add_params, 2, htmlspecialchars(is_constant($splitted[2])), $type1);
        create_xml_arguments($add_params, 3, htmlspecialchars(is_constant($splitted[3])), $type2);
    }
    else
    {
        error_log("Wrong format \"$splitted[0]\".\n");
        exit(ERROR_LEXICAL_OR_SYNTEX);
    }
}

//Adds and sets an element for xml.
function create_xml_functions($order,$opcode)
{
    global $xml, $xml_node;
    
    //Creates an element.
    $xml_function=$xml->createElement("instruction");
    //Sets the value of the attribute with the specified name.
    $xml_function->setAttribute("order", $order);
    $xml_function->setAttribute("opcode", $opcode);
    
    //Creates a new list of children and retuns it.
    return $xml_node->appendChild($xml_function);
}

//Adds argument for xml function.
function create_xml_arguments($xml_function, $order, $function, $type)
{
    global $xml;
    //Creates an element.
    $xml_argument = $xml->createElement("arg$order", $function);
    //Sets the value of the attribute with the specified name.
    $xml_argument->setAttribute('type', $type);
    //Appends a child to an existing list of children.
    $xml_argument=$xml_function->appendChild($xml_argument);
}

//Specifies the type.
function is_type($type)
{
    if(is_variable($type))
        return "var";

    elseif(preg_match('/^nil@nil$/', $type))
        return "nil";

    elseif(preg_match('/^int@[+-]?[\d]+$/', $type))
        return "int";

    elseif(preg_match('/^bool@(true|false)$/', $type))
        return "bool";

    elseif(preg_match('/^string@/', $type))
        return "string";
    //For float.
    // elseif(preg_match('/^float@0x([a-f]|[\d])(\.[\d|a-f]*)?p(\+|-)?[\d]*$/i', $type))
    //     return "float";
    return false;
}

//Checks if the variable is valid.
function is_variable($variable)
{
    return preg_match('/(GF|LF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*/', $variable) ? true : false;
}

//Сhecks if the label is valid.
function is_label($label)
{
    return preg_match('/^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$/', $label) ? true : false;
}

//Fixes constant.
function is_constant($const)
{
    return preg_replace('/^(nil|int|bool|string)@/', "", $const);
}

//Helps with adding parametrs for xml function.
function params($counters, $splitted)
{
    return create_xml_functions($counters->instructions, $splitted);
}

//Writing statistics to a file.
function print_stats($if_stats, $counters, $file)
{
    //If the user requested statistics.
    if($if_stats)
    {
        //Opens a file for writing.
        $file = fopen($file, "w");

        //Writes statistics to the required file, preserving the sequence.
        for($i = 0; $i != count($counters->stats_arr); $i++)
        {
            if($counters->stats_arr[$i] == 'loc')
                fprintf($file, "$counters->instructions\n");

            elseif($counters->stats_arr[$i] == 'comments')
                fprintf($file, "$counters->comments\n");

            elseif($counters->stats_arr[$i] == 'labels')
            {
                fprintf($file, "%d\n", $counters->label);
            }
            elseif($counters->stats_arr[$i] == 'jumps')
                fprintf($file, "$counters->jumps\n");
        }
        //Deletes all buffers that are associated with the required file.
        fclose($file);
    }
}
?>