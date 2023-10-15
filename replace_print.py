
import re
import sys

# the target is to replace statements of the form
#           System.out.print(left + "..." + mid_1 + "..." + mid_2 + "..." ... + mid_n + "..." + right);
def replace_print(print_arg):
    print_str = print_arg
    # merge "..." + "..."
    print_str = re.sub("\"[ \n\t]*\+[ \n\t]*\"", "", print_str, re.DOTALL)
    print_str_args = ""

    # find left
    left_pattern = "^[^\"].*?\+[ \n\t]*\""
    left_match = re.search(left_pattern, print_str, re.DOTALL)
    # substitute left with "{}" and add left in the list of arguments in Pantools.logger
    if left_match:
        print_str = "{}" + print_str[left_match.end(0):] #print_str.replace(print_str[left_match.start(0):left_match.end(0)], "{}", 1)
        print_str_args += ", " + left_match.group(0).rstrip(" +\"\n\t")

    # find mid_1, mid_2 ... mid_n
    middle_pattern = "\"[ \n\t]*\+.*?\+[ \n\t]*\""
    middle_matches = re.findall(middle_pattern, print_str, re.DOTALL)
    # substitute mid with "{}" and add mid in the list of arguments in Pantools.logger
    for match in middle_matches:
        match_trunc = match
        #---------to handle the case if the statments contains something like "+ ........." + mid_i
        count_total_quotes =match_trunc.count('"')
        count_single_quotes = match_trunc.count('\\"') + match_trunc.count('\'\"\'')
        while ((count_total_quotes - count_single_quotes)%2 != 0):
            match_trunc = match_trunc[(match_trunc[1:].index('"')) + 1:]
            count_total_quotes = match_trunc.count('"')
            count_single_quotes = match_trunc.count('\\"') + match_trunc.count('\'\"\'')
        #----------------------------------------------------------------------------------------------
        print_str = print_str.replace(match_trunc, "{}", 1)
        print_str_args += ", " + match_trunc.strip(" +\"\n\t")

    # find right
    right_pattern = "\"[ \n\t]*\+.*?[^\"]$"
    right_match = re.search(right_pattern, print_str, re.DOTALL)
    # substitute right with "{}" and add right in the list of arguments in Pantools.logger
    if right_match:
        print_str = print_str[:right_match.start(0)] + "{}"#print_str.replace(print_str[right_match.start(0):right_match.end(0)], "{}", 1)
        print_str_args += ", " + right_match.group(0).lstrip(" +\"\n\t")

    # remove any spaces, TABs and newlines. Forgot why I need this
    print_str = re.sub("\"[ \n\t]*\+[ \n\t]*\"", "", print_str)
    return [print_str, print_str_args]


#this is for relpacing System.out.printf or String.format statements
def replace_printf(print_arg):
    print_str = print_arg
    print_str = re.sub("%[^ n\t\"\']+", "{}", print_str)
    print_str = print_str.replace("%n", "\\n")
    return print_str


def replace(in_file):
    #open input file
    fh_read = open(in_file, "r")
    # open input file for writing
    fh_write = open (in_file.rstrip(".java") + "_replaced.java", "w")

    while line := fh_read.readline():
        line_to_write = line
        if ("System.out." in line) or  ("System.err." in line):
            multiline = line

            # For the case of multline print statement
            while not re.search("\)[ ]*;", multiline):
                multiline += fh_read.readline()
            # Extract the print statement from line/multiline
            print_statement_match_obj = re.search("System.+\(.*\)[ ]*;", multiline, re.DOTALL)
            print_statement = multiline[print_statement_match_obj.start(): print_statement_match_obj.end()]
            # Extract the print statement argument
            print_arg = re.search('\((.*)\)', print_statement, re.DOTALL).group(0)[1:-1]

            # To skip empty arguments and print statements wit "\r"
            if (not print_arg) or ("\\r" in print_arg):
                fh_write.write(multiline)
                continue

            # sometimes the statement is like "System.out.print(a_variable)
            add_quotes = False
            if "\"" in print_arg:
                add_quotes = True
            if (("System.out.print" in print_statement) or ("System.err.print" in print_statement)) and (("String.format" not in print_statement) and ("System.out.printf" not in print_statement) and ("System.err.printf" not in print_statement)):
                [print_str, print_str_args] = replace_print(print_arg)
                if add_quotes:
                    log_statement = "Pantools.logger.info(\"" + print_str.strip("\"") + "\"" + print_str_args + ");"
                    line_to_write = multiline.replace(print_statement,log_statement)
                else:
                    log_statement = "Pantools.logger.info(" + print_str.strip("\"") + print_str_args + ");"
                    line_to_write = multiline.replace(print_statement, log_statement)

            elif ("System.out.printf" in print_statement) or ("System.err.printf" in print_statement) or ("String.format" in print_statement):
                line_to_write = replace_printf(print_arg)
                line_to_write = multiline.replace(print_statement,"Pantools.logger.info(" + line_to_write +");")

            #to detect if the next statement is System.exit(). For now it cannot detect System.exit() as the next command if there is a multiline-comment in-between
            exit_line = False
            while next_line := fh_read.readline():
                if "System.exit" in next_line:
                    exit_line = True
                    fh_read.seek(fh_read.tell() - len(next_line))
                    break
                elif next_line.lstrip(" \t") == "\n":
                    line_to_write += next_line
                    continue
                elif (next_line.lstrip(" \t")).startswith("//"):
                    line_to_write += next_line
                    continue
                else:
                    fh_read.seek(fh_read.tell() - len(next_line))
                    break

            if exit_line:
                line_to_write = line_to_write.replace("Pantools.logger.info", "Pantools.logger.error")
            print("Old: " + multiline)
            print("New: " + line_to_write)

        # write the Pantools.looger statement in the file  <File name>_replaced.java
        fh_write.write(line_to_write)

    fh_read.close()
    fh_write.close()




if __name__ == '__main__':
    replace(sys.argv[1])


