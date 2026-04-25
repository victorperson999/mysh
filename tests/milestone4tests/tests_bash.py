# Tests to check whether bash commands are actually fetched
from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import * 

def _test_commands_exist(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Bash Builtins are fetched and do not report errors")

  try:
    p = start('./mysh')
    write(p,"pwd")
    sleep(command_wait)
    write(p,"head -n 1 mysh.c")
    sleep(command_wait)
    write(p,"sleep 0.0001")
    sleep(command_wait)
    if not stderr_empty(p):
        finish(comment_file_path, "NOT OK")
        return
    finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  

def _test_fictional_fail(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Command that do not exist report errors")

  try:
    p = start('./mysh')
    write(p,"wd")
    sleep(command_wait)
    if stderr_empty(p):
      finish(comment_file_path, "NOT OK")
      return
    else:
      while not stderr_empty(p):
          read_stderr(p)
    write(p,"clea")
    sleep(command_wait)
    if stderr_empty(p):
      finish(comment_file_path, "NOT OK")
      return
    finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
def _test_tail(comment_file_path, student_dir, command_wait=0.05, max_length=20):
  start_test(comment_file_path, "tail command works correctly")

  # Create a file 
  fptr = open(student_dir + "/testfile.txt", "w")
  fptr.write("word1\nword2\nword3\nword4\nword5\nword6\n")
  fptr.close()

  try:
    p = start('./mysh')
    write(p, "tail -n 1 testfile.txt")    
    output = read_stdout(p)
    if "word6" in output and len(output) < max_length:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_file(student_dir + "/testfile.txt")


def _test_pipe_tail(comment_file_path, student_dir, command_wait=0.05, max_length=20):
  start_test(comment_file_path, "tail command supports pipes")

  # Create a file 
  fptr = open(student_dir + "/testfile.txt", "w")
  fptr.write("word1\nword2\nword3\nword4\nword5\nword6\n")
  fptr.close()

  try:
    p = start('./mysh')
    write(p, "cat testfile.txt | tail -n 1")    
    output = read_stdout(p)
    if "word6" in output and len(output) < max_length:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_file(student_dir + "/testfile.txt")

def _test_pipe_head(comment_file_path, student_dir, command_wait=0.05, max_length=20):
  start_test(comment_file_path, "head command supports pipes")

  # Create a file 
  fptr = open(student_dir + "/testfile.txt", "w")
  fptr.write("word1\nword2\nword3\nword4\nword5\nword6\n")
  fptr.close()

  try:
    p = start('./mysh')
    write(p, "cat testfile.txt | head -n 1")    
    output = read_stdout(p)
    if "word1" in output and len(output) < max_length:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_file(student_dir + "/testfile.txt")

def test_bash_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Bash Commands are executed correctly")
  start_with_timeout(_test_commands_exist, comment_file_path, student_dir)
  start_with_timeout(_test_fictional_fail, comment_file_path, student_dir)
  start_with_timeout(_test_tail, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Bash Commands support pipes")
  start_with_timeout(_test_pipe_tail, comment_file_path, student_dir)
  start_with_timeout(_test_pipe_head, comment_file_path, student_dir)
  end_suite(comment_file_path)
