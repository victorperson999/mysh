from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, PIPE 
import os
import shutil
import pty
import datetime
import sys
from time import sleep 
import subprocess
from random import randint 
from tests_helpers import *  

def _test_multiline_input(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Test inputting multiple lines at once")
  try:
    p = start('./mysh')
    write(p,"echo here\necho there")
    sleep(command_wait)
    sleep(command_wait)
    output1 = read_stdout(p)
    output1 += "\n" + read_stdout(p)

    write(p,"echo still working")
    output2 = read_stdout(p)
    if "here\nmysh$ there" not in output1 or "still working" not in output2:
      finish_process(comment_file_path, "NOT OK", p) 
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p) 
    return 

  if has_memory_leaks(p):
    finish_process(comment_file_path, "NOT OK", p)
  else:
    finish_process(comment_file_path, "OK", p)

def test_general_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Multiline input tests")
  start_with_timeout(_test_multiline_input, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)