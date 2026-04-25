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



def _test_echo_echo_cat_wc(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Four-level pipe with echo, cat, and wc")
    try:
        p = start('./mysh')
        write(p,"echo a | cat | cat | wc")
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

def _test_cat_cat_wc_cat(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Four level pipe involving cat and wc")
    fptr = open(student_dir + "/testfile.txt", "w")
    fptr.write("word1 word2 word3\n")
    fptr.close()

    try:
        p = start('./mysh')
        write(p,"cat testfile.txt | cat | wc | cat")
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

def _test_bg_cat_wc_no_content(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Test command with cat and wc involving pipes and background has no access to stdin")

    try:
        p = start('./mysh')
        write(p,"cat | wc &")
        sleep(command_wait)
        read_stdout(p)  # job message
        output1 = read_stdout(p)
        if "word count 0" not in output1:
            finish(comment_file_path, f"NOT OK") 
            return
        output2 = read_stdout(p)
        if "character count 0" not in output2:
            finish(comment_file_path, f"NOT OK") 
            return
        output3 = read_stdout(p)
        if "newline count 0" not in output3:
            finish(comment_file_path, f"NOT OK") 
            return
        
        write(p,"") # to trigger catch_children()
        output4 = read_stdout(p)
        if "[1]+ Done" not in output4 or "cat | wc" not in output4:
            finish(comment_file_path, "NOT OK") 
            return
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_sleep_piped_to_ps_with_existing_bg_processes(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Test ps only lists jobs spwaned by the process running ps")

    try:
        p = start('./mysh')
        write(p,"sleep 10 &")
        sleep(command_wait)
        read_stdout(p) # job message
        write(p, "ps")
        sleep(command_wait)
        output1 = read_stdout(p)
        if "sleep" not in output1:
            finish_process(p, comment_file_path, f"NOT OK")
            return
        write(p,"echo hi | ps")
        sleep(command_wait)
        output = read_stdout(p) # should timeout as we only expect 'mysh$ ' as output because ps should list no jobs
        finish(comment_file_path, f"NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_large_amount_of_data_blocks_pipe(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Test sending large amount of data blocks pipe when next process is not reading from it")

    try:
        p = start('./mysh')
        write(p,"cat /home/bhavsa72/lesshugefile.txt | sleep 3 &") # 63KB file with lorem ipsum
        sleep(command_wait)
        read_stdout(p) # job message

        sleep(0.2)
        write(p, "") # trigger catch_children()
        sleep(command_wait)
        write(p, "ps")
        sleep(command_wait)
        output1 = read_stdout(p)
        if "cat /home/bhavsa72/lesshugefile.txt" in output1:
             finish_process(comment_file_path, f"NOT OK", p)
             return
        sleep(3)
        write(p, "") # to trigger catch_children()
        sleep(command_wait)
        output2 = read_stdout(p)
        if "[1]+ Done" not in output2 or "cat /home/bhavsa72/lesshugefile.txt | sleep 3" not in output2:
            finish_process(comment_file_path, f"NOT OK", p)
            return
        
        write(p,"cat /home/bhavsa72/hugefile.txt | sleep 3 &") # 65KB file with lorem ipsum
        sleep(command_wait)
        read_stdout(p) # job message
        
        sleep(0.2)
        write(p, "") # to trigger catch_children()
        sleep(command_wait)
        write(p, "ps")
        output3 = read_stdout(p)
        output4 = read_stdout(p)
        if "cat /home/bhavsa72/hugefile.txt" not in output3 and "cat /home/bhavsa72/hugefile.txt" not in output4:
            finish_process(comment_file_path, f"NOT OK", p)
            return
        if "sleep 3" not in output3 and "sleep 3" not in output4:
            finish_process(comment_file_path, f"NOT OK", p)
            return
        
        sleep(3)
        write(p, "") # to trigger catch_children()
        sleep(command_wait)
        output5 = read_stdout(p)
        if "[1]+ Done" not in output5 and "cat /home/bhavsa72/hugefile.txt | sleep 3" not in output5:
            finish_process(comment_file_path, f"NOT OK", p)
            return
        
        finish(comment_file_path, f"OK")

    except Exception as e:
        finish(comment_file_path, f"NOT OK")

def _test_large_amount_of_data_no_pipe_block(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Test sending large amount of data doesn't blocks pipe when next process is reading from it")

    try:
        p = start('./mysh')
        write(p,"cat /home/bhavsa72/hugefile.txt | wc | sleep 3 &") # 65KB file with lorem ipsum
        sleep(command_wait)
        read_stdout(p) # job message
        sleep(0.2)
        write(p, "") # trigger catch_children()
        sleep(command_wait)
        write(p, "ps")
        sleep(command_wait)
        output1 = read_stdout(p)
        if "cat /home/bhavsa72/hugefile.txt" in output1 or "wc" in output1:
            finish_process(comment_file_path, f"NOT OK", p)
            return
        
        sleep(3)
        write(p, "") # trigger catch_children()
        sleep(command_wait)
        output2 = read_stdout(p)
        if "[1]+ Done" not in output2 or "cat /home/bhavsa72/hugefile.txt | wc | sleep 3" not in output2:
            finish_process(comment_file_path, f"NOT OK", p)
            return
        finish(comment_file_path, f"OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def test_milestone4_hidden_suite(comment_file_path, student_dir):
    
    start_suite(comment_file_path, "Hidden - 4 level pipes")
    start_with_timeout(_test_echo_echo_cat_wc, comment_file_path, student_dir)
    start_with_timeout(_test_cat_cat_wc_cat, comment_file_path, student_dir)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - No access to stdin for background processes")
    start_with_timeout(_test_bg_cat_wc_no_content, comment_file_path, student_dir)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - Correct functionality of ps with pipes v2")
    start_with_timeout(_test_sleep_piped_to_ps_with_existing_bg_processes, comment_file_path, student_dir, timeout=5, timeoutFeedback="OK\n")
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - Test effects of large amount of data on pipe blocking")
    start_with_timeout(_test_large_amount_of_data_blocks_pipe, comment_file_path, student_dir, timeout=7)
    start_with_timeout(_test_large_amount_of_data_no_pipe_block, comment_file_path, student_dir, timeout=5)
    end_suite(comment_file_path)

    remove_folder(student_dir + "/testfolder")
    
