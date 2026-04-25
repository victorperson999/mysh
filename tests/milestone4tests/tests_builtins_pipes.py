from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import * 

def reset_folder(folder_path):
    os.popen('rm -rf {}'.format(folder_path)).read()   # Remove the directory so we can recreate it
    os.popen('mkdir {}'.format(folder_path)).read()


def setup_folder_structure(folder_root_path: str, files: list):
    """
    Create a file structure.
    folder_root_path represents the root of the file structure. 
    files is a list of files or directories. 
    Directories have the form {name: subfiles}. Files are strings. 
    """
    reset_folder(folder_root_path)
    for file in files:
        if isinstance(file, dict):
          file_name = list(file.keys())[0]
          setup_folder_structure(folder_root_path + "/" + file_name, file[file_name])
        else:
          command = "touch {}/{}".format(folder_root_path, file) 
          os.popen(command) 

def _test_wc_ls(comment_file_path, student_dir):
  start_test(comment_file_path, "Pipe the output of ls to wc displays valid counts")
  
  try:
    p = start('./mysh')
    write(p,"ls | wc")

    # Read standard output to verify the counts are displays
    output1 = read_stdout(p)
    if "word count" not in output1:
        finish(comment_file_path, "NOT OK")
        return 
    output2 = read_stdout(p)
    if "character count" not in output2:
        finish(comment_file_path, "NOT OK")
        return 
    output3 = read_stdout(p)
    if "newline count" not in output3:
        finish(comment_file_path, "NOT OK")
        return 
    
    finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_wc_echo(comment_file_path, student_dir):
  start_test(comment_file_path, "Pipe the output of echo to wc displays valid counts")
  
  try:
    p = start('./mysh')
    write(p,"echo sampletext | wc")

    # Read standard output to verify the counts are displays
    output1 = read_stdout(p)
    if "word count 1" not in output1:
        finish(comment_file_path, "NOT OK")
        return 
    output2 = read_stdout(p)
    if "character count 11" not in output2:
        finish(comment_file_path, "NOT OK")
        return 
    output3 = read_stdout(p)
    if "newline count 1" not in output3:
        finish(comment_file_path, "NOT OK")
        return 
    finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_ls_pipe(comment_file_path, student_dir):
    start_test(comment_file_path, "Piping the output of ls to ls works the same as normal ls")
    setup_folder_structure(student_dir + "/testfolder", [])   # A single folder
    try:
        p = start('./mysh')
        write(p,"ls testfolder | ls testfolder")   
        output = read_stdout(p).replace('mysh$ ', '')
        output2 = read_stdout(p).replace('mysh$ ', '')
        output_files = set([output, output2])
        if output_files == set(['.', '..']):
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_cd_pipe(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Pipes involving cd do not change the current directory")
    setup_folder_structure(student_dir + "/testfolder", ["subfile"])   # A single folder with one file
  
    try:
        p = start('./mysh')
        write(p,"cd testfolder")
        sleep(command_wait)
        write(p,"cd .. | cd ..")    # Does not change current directory. 
        sleep(command_wait)
        write(p,"ls")
        sleep(command_wait)
        expected_output = set([".", "..", "subfile"])
        expected_output_lines = len(expected_output)
        output_files = []
        for _ in range(expected_output_lines):
            line = read_stdout(p).replace('mysh$ ', '')
            output_files.append(line)

        output_files = set(output_files)
        if output_files == expected_output:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_echo_pipe(comment_file_path, student_dir):
    start_test(comment_file_path, "Piping echo to echo works the same as normal echo")
    try:
        p = start('./mysh')
        write(p,"echo text1 | echo text2")   
        output = read_stdout(p)
        if "text1" not in output and "text2" in output:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_echo_pipe_v2(comment_file_path, student_dir):
    start_test(comment_file_path, "Piping echo to echo works the same as normal echo")
    try:
        p = start('./mysh')
        write(p,"echo text2 | echo text1")   
        output = read_stdout(p)
        if "text2" not in output and "text1" in output:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def _test_cat_echo(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Cat reading input from echo")

    try:
        p = start('./mysh')
        write(p,"echo sample text | cat")
        output1 = read_stdout(p)
        if "sample text" not in output1:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_cat_wc(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Cat builtin supports pipes")
    fptr = open(student_dir + "/testfile.txt", "w")
    fptr.write("word1 word2 word3\n")
    fptr.close()

    try:
        p = start('./mysh')
        write(p,"cat testfile.txt | wc")
        output1 = read_stdout(p)
        if "word count" not in output1:
            finish(comment_file_path, "NOT OK") 
            return 
        output2 = read_stdout(p)
        if "character count" not in output2:   
            finish(comment_file_path, "NOT OK") 
            return 
        output3 = read_stdout(p)
        if "newline count" not in output3:
            finish(comment_file_path, "NOT OK") 
            return 
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")

# Pipes involving variables

def _test_variable_echo(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Variable declaration in pipes is not reflected")

    try:
        p = start('./mysh')
        write(p,"x=5 | echo $x")
        output = read_stdout(p)
        if "5" in output:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")



def _test_redefine_echo(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Variable re-define in pipes is not reflected")

    try:
        p = start('./mysh')
        write(p, "x=5")
        sleep(command_wait)
        write(p,"x=6 | echo $x")
        output = read_stdout(p)
        if "6" in output or "5" not in output:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")


# Pipe Error Handling 
def _test_long_line(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Pipe line cannot exceed the character limit")

    try:
        p = start('./mysh')
        write(p,"echo bigword1bigword1bigword1 | echo bigword2bigword2bigword2 | echo bigword3bigword3bigword3 | echo bigword4bigword4bigword4 | echo bigword5bigword5bigword5")
        output = read_stderr(p)
        if "ERROR: input line too long" not in output:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_error_chain(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "A failing command does not stop the pipe chain")

    try:
        p = start('./mysh')
        write(p,"cat adsfd | echo hello")
        error1 = read_stderr(p)
        output = read_stdout(p)
        if "ERROR: Cannot open file" not in error1:
            finish(comment_file_path, "NOT OK") 
            return 
        
        if "hello" not in output:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")


# Pipe Edge Cases

def _test_no_space(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Spaces are not required within pipes")

    try:
        p = start('./mysh')
        write(p,"echo sample text|cat")
        output1 = read_stdout(p)
        if "sample text" not in output1:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def _test_non_existant(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Pipe to a command that does not exist reports unknown error")

    try:
        p = start('./mysh')
        write(p,"echo sample | fakecommand")
        output1 = read_stderr(p)
        if "ERROR: Unknown command: fakecommand" not in output1:
            finish(comment_file_path, "NOT OK") 
            return 
        
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")




# Three Level Pipes

def _test_cat_cat_wc(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Cat builtin supports nested pipes")
    fptr = open(student_dir + "/testfile.txt", "w")
    fptr.write("word1 word2 word3\n")
    fptr.close()

    try:
        p = start('./mysh')
        write(p,"cat testfile.txt | cat | wc")
        output1 = read_stdout(p)
        if "word count" not in output1:
            finish(comment_file_path, "NOT OK") 
            return 
        output2 = read_stdout(p)
        if "character count" not in output2:   
            finish(comment_file_path, "NOT OK") 
            return 
        output3 = read_stdout(p)
        if "newline count" not in output3:
            finish(comment_file_path, "NOT OK") 
            return 
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_echo_cat_wc(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Three-level pipe with echo, cat, and wc")
    try:
        p = start('./mysh')
        write(p,"echo a | cat | wc")
        output1 = read_stdout(p)
        if "word count 1" not in output1:
            finish(comment_file_path, "NOT OK") 
            return 
        output2 = read_stdout(p)
        if "character count 2" not in output2:   
            finish(comment_file_path, "NOT OK") 
            return 
        output3 = read_stdout(p)
        if "newline count 1" not in output3:
            finish(comment_file_path, "NOT OK") 
            return 
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")
    
def _test_sleep_piped_to_ps(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Test correct output of ps when sleep is piped into ps")

    try:
        p = start('./mysh')
        write(p,"sleep 3 | ps")
        sleep(command_wait + 3)
        output = read_stdout(p) # should timeout as we only expect 'mysh$ ' as output because ps should list no jobs
        finish(comment_file_path, f"NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def test_builtin_pipes_suite(comment_file_path, student_dir):
    start_suite(comment_file_path, "Sample echo pipes")
    start_with_timeout(_test_echo_pipe, comment_file_path,  student_dir)
    start_with_timeout(_test_echo_pipe_v2, comment_file_path,  student_dir)
    end_suite(comment_file_path)


    start_suite(comment_file_path, "Sample ls & cd pipes")
    start_with_timeout(_test_ls_pipe, comment_file_path, student_dir)
    start_with_timeout(_test_cd_pipe, comment_file_path, student_dir)
    end_suite(comment_file_path)


    start_suite(comment_file_path, "Sample wc pipe")
    start_with_timeout(_test_wc_ls, comment_file_path, timeoutFeedback="OK\n")
    start_with_timeout(_test_wc_echo, comment_file_path)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Sample cat pipes")
    start_with_timeout(_test_cat_echo, comment_file_path,  student_dir)
    start_with_timeout(_test_cat_wc, comment_file_path,  student_dir)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Pipes with variables")
    start_with_timeout(_test_variable_echo, comment_file_path,  student_dir)
    start_with_timeout(_test_redefine_echo, comment_file_path,  student_dir)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Pipes Error Handling")
    start_with_timeout(_test_long_line, comment_file_path, student_dir)
    start_with_timeout(_test_error_chain, comment_file_path, student_dir)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Pipe Edge Cases")
    start_with_timeout(_test_no_space, comment_file_path, student_dir)
    start_with_timeout(_test_non_existant, comment_file_path, student_dir)
    end_suite(comment_file_path)

    
    start_suite(comment_file_path, "Three Level pipes")
    start_with_timeout(_test_cat_cat_wc, comment_file_path, student_dir)
    start_with_timeout(_test_echo_cat_wc, comment_file_path, student_dir)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Correct functionality of ps with pipes")
    start_with_timeout(_test_sleep_piped_to_ps, comment_file_path, student_dir, timeout=5, timeoutFeedback="OK\n")
    end_suite(comment_file_path)
    
    remove_folder(student_dir + "/testfolder")
    
