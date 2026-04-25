from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import shutil
import pty
import datetime
import sys
from time import sleep 
import subprocess
from pathlib import Path
from random import randint 
from tests_helpers import *  

MEMORY_THRESHHOLD = 500
  
def _test_long_declare(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Long variable declaration is prohibited")
  try:
    p = start('./mysh')
    variable_declaration = "x" * 200 + "=1"
    # print("write long")
    write(p,variable_declaration)
    sleep(command_wait)
    output = read_stderr(p)
    if "ERROR" not in output:
        # print("failed")
        finish(comment_file_path, "NOT OK")
        return  

    # Verify the shell can exit with no memory leaks.
    if has_memory_leaks(p):
      #print("mem leak")
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    # print("exception")
    print(e)
    finish(comment_file_path, "NOT OK")
    return 
  

# i.e., just:
# x=3
# y=$x
# echo $y
# … should result in 3.
# And:
# x=3
# y=x
# echo $y
def _test_variable_def_expansion(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Test variable expansion during variable assignment")
  try:
    p = start('./mysh')
    
    # print("writing x")
    write(p,"x=3")
    # print("waiting")
    sleep(command_wait)

    # print("writing y assignment 1")
    write(p,"y=$x")
    # print("waiting")
    sleep(command_wait)
    # print("writing echo y 1")
    write(p,"echo $y")
    out_1 = read_stdout(p).strip("\nmysh$ ").strip("\n").strip()

    # print("writing y assignment 2")
    write(p,"y=x")
    # print("waiting")
    sleep(command_wait)
    # print("writing echo y 2")
    write(p,"echo $y")
    out_2 = read_stdout(p).strip("\nmysh$ ").strip("\n").strip()

    # print(out_1)
    # print(out_2)

    if out_1 != "3" or out_2 != "x":
      finish(comment_file_path, "NOT OK") 
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    # print("memory leak")
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

  
def _test_redefine_100(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Declare, redefine and access 100 variables")
  try:
    p = start('./mysh')
    failed = False 
    for i in range(100):
      random_number = randint(1, 100)
      value = "var{}".format(random_number)
      write(p,"x{}={}".format(i, value))
      
      sleep(command_wait)
      # print(f"sleep 1 {i}")
      value = "var{}".format(2*i)   # Change to even number
      write(p,"x{}={}".format(i, value))
      
      sleep(command_wait)
      # print(f"sleep 2 {i}")
      write(p,"echo $x{}".format(i))
      output = read_stdout(p)
      if value not in output:
        # print(f"failed at {i}")
        # print(value)
        # print(output)
        failed = True 
    # print("finished")
    if failed:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    # print("memory leak")
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def _test_expansion_into_assignment(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests expansion into an assignment statement doesn't work")
  try:
    p = start('./mysh')
    write(p,f"name=x")
    sleep(command_wait)
    write(p,f"$name=22")
    sleep(command_wait)
    out1 = read_stderr(p)
    write(p,f"echo $x")
    sleep(command_wait)
    out2 = read_stdout(p).strip("mysh$ ")
    if "ERROR" not in out1 or "22" in out2:
      finish(comment_file_path, f"NOT OK") 
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def _test_no_setenv_or_getenv(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Test there is no use of setenv or getenv")
  try:
    logFile = Path('ltrace.log')
    logFile.touch()
    env = os.environ.copy()
    env["LSAN_OPTIONS"] = "detect_leaks=0" # needed because ltrace can't run with leak sanitizer
    p = subprocess.Popen(['ltrace', '-o', 'ltrace.log', '-f', '-e', 'setenv', '-e', 'getenv', './mysh'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env)
    
    # aim to trigger all major functionalities of mysh to test for use of getenv or setenv anywhere
    write(p,"echo here")
    sleep(command_wait)

    write(p,"x=5")
    sleep(command_wait)

    write(p,"echo $x")
    sleep(command_wait)

    write(p, "exit")
    sleep(command_wait)
    log = open('ltrace.log').read()

    if "setenv" in log or ("getenv" in log and "libubsan.so.1->getenv" not in log):
      if logFile.exists():
        logFile.unlink()
      finish(comment_file_path, f"NOT OK")
    else:
      if logFile.exists():
        logFile.unlink()
      finish(comment_file_path, f"OK")
  except Exception as e:
    if logFile.exists():
        logFile.unlink()
    finish(comment_file_path, "NOT OK") 

def _test_dynamic_memory_allocation(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Test there is use of dynamic memory management")
  try:
    logFile = Path('ltrace.log')
    logFile.touch()
    env = os.environ.copy()
    env["LSAN_OPTIONS"] = "detect_leaks=0" # needed because ltrace can't run with leak sanitizer
    p = subprocess.Popen(['ltrace', '-o', 'ltrace.log', '-f', '-e', 'malloc', '-e', 'calloc', '-e', 'realloc', '-e', 'strdup', '-e', 'strndup', './mysh'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env)
    write(p,"x=5")
    sleep(command_wait)
    sleep(command_wait)

    write(p, "exit")
    sleep(command_wait)
    sleep(command_wait)
    log = open('ltrace.log').read()

    if "malloc" not in log and "calloc" not in log and "realloc" not in log and "strdup" not in log and "strndup" not in log:
      if logFile.exists():
       logFile.unlink()
      finish(comment_file_path, f"NOT OK")
    else:
      if logFile.exists():
        logFile.unlink()
      finish(comment_file_path, f"OK")
  except Exception as e:
    if logFile.exists():
        logFile.unlink()
    finish(comment_file_path, f"NOT OK") 
    return 

def test_variables_hidden_suite(comment_file_path, student_dir):

  start_suite(comment_file_path, "Hidden - Variable Definition Error Handling")
  start_with_timeout(_test_long_declare, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - Variable Expansion in Assignment")
  start_with_timeout(_test_variable_def_expansion, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - Large Redefine")
  start_with_timeout(_test_redefine_100, comment_file_path, timeout=20)  # Larger timeout
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - Expansion into assignment")
  start_with_timeout(_test_expansion_into_assignment, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - Library calls")
  start_with_timeout(_test_no_setenv_or_getenv, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_dynamic_memory_allocation, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)  
