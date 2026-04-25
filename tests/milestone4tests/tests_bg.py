from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import *


def _test_simple_bg(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "A simple background echo correctly completes")

  try:
    p = start('./mysh')
    write(p,"echo hello &")
    sleep(command_wait)
    output1 = read_stdout(p)
    output2 = read_stdout(p)
    if ("[1]" in output1 or "hello" in output1) and \
       ("[1]" in output2 or "hello" in output2):
      if not stderr_empty(p):
        finish(comment_file_path, "NOT OK")
        return
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_responsive_shell(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Shell can execute other commands while a background process runs")

  try:
    p = start('./mysh')
    write(p,"sleep 5 &")
    sleep(command_wait)
    read_stdout(p)
    write(p,"echo testing")
    sleep(command_wait)
    echo_output = read_stdout(p)
    if "testing" in echo_output:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

def _test_multiple_bg(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Shell can execute multiple background processes")

  try:
    p = start('./mysh')
    write(p,"sleep 10 &")
    sleep(command_wait)
    write(p,"sleep 10 &")
    sleep(command_wait)
    write(p,"sleep 10 &")
    sleep(command_wait)
    output1 = read_stdout(p)
    output2 = read_stdout(p)
    output3 = read_stdout(p)
    if "[1]" in output1 and "[2]" in output2 and "[3]" in output3: 
      if not stderr_empty(p):
        finish(comment_file_path, "NOT OK")
        return
      finish(comment_file_path, "OK")
    elif "[1]" in output2 or "[1]" in output3 or \
    "[2]" in output1 or "[2]" in output3 or \
    "[3]" in output1 or "[3]" in output2:
      finish(comment_file_path, "NOT OK (BG OUTPUT)")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

# ps tests

def _test_single_ps(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "ps command shows a background process")

  try:
    p = start('./mysh')
    write(p,"sleep 5 &")
    sleep(command_wait)
    read_stdout(p)
    sleep(command_wait)
    write(p,"ps")
    ps_output = read_stdout(p)
    if "sleep" in ps_output:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_multiple_ps(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "ps command shows multiple background processes")

  try:
    p = start('./mysh')
    write(p,"sleep 5 &")
    sleep(command_wait)
    read_stdout(p)
    sleep(command_wait)
    write(p,"sleep 5 &")
    read_stdout(p)
    sleep(command_wait)
    write(p,"ps")
    ps_output1 = read_stdout(p)
    ps_output2 = read_stdout(p)
    if "sleep" not in ps_output1 or "sleep" not in ps_output2:
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


# Background jobs complete cases

def _test_bg_completes(comment_file_path, student_dir, command_wait=0.05, length_cutoff=60):
  start_test(comment_file_path, "Background process completes with a corresponding DONE message")

  try:
    p = start('./mysh')
    write(p,"sleep 0.5 &")
    read_stdout(p)   # Background process creation message
    sleep(1)   # Wait while background job completes 
    write(p, "x=1")
    output = read_stdout(p)
    if "[1]+ Done" in output and len(output) < length_cutoff: 
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    print("Error is ", e)
    finish(comment_file_path, "NOT OK")

# Note that our implementation displays DONE whenever a process completes 
# This is a simplified version of bash.
def _test_bg_terminates(comment_file_path, student_dir, command_wait=0.05, length_cutoff=70):
  start_test(comment_file_path, "Background process is DONE after terminated by a kill")

  try:
    p = start('./mysh')
    write(p,"sleep 1000 &")
    output = read_stdout(p)   # Background process creation message
    output = output.strip('\n')
    closing_bracket = output.index("]")
    pid_start = closing_bracket + 2
    pid = int(output[pid_start:])
    write(p, "kill {}".format(pid))
    sleep(command_wait)
    write(p, "x=1")
    output = read_stdout(p)
    if "[1]+ Done" in output and "sleep 1000" in output and len(output) < length_cutoff:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


# Edge Cases

def _test_count_reset(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Background process counts reset to 1 after all processes complete")

  try:
    p = start('./mysh')
    write(p,"sleep 0.6 &")
    sleep(command_wait)
    
    write(p,"sleep 0.5 &")
    sleep(command_wait)
    # Ignore creation messages 
    read_stdout(p)  
    read_stdout(p)   

    sleep(1)   # Wait while background jobs complete
    write(p, "x=1")
    # Ignore done messages 
    read_stdout(p)
    read_stdout(p)
    
    # Create another process. Background process number should be 1.
    write(p,"sleep 0.5 &")
    output = read_stdout(p)
    if "[1]" in output:  # i.e., "[3]" not in output:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK (expected [1] sleep ...)")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

def _test_exceed_limits(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Background process line cannot exceed character limits")

  try:
    p = start('./mysh')
    message = "a" * 150
    write(p, "echo {} &".format(message))

    output = read_stderr(p)
    if "ERROR: input line too long" in output:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

# BG integration tests

def _test_bg_pipes(comment_file_path, student_dir, command_wait=0.05, length_cutoff=35):
  start_test(comment_file_path, "Pipes work correctly while background process runs")

  try:
    p = start('./mysh')
    write(p, "sleep 100 &")
    sleep(command_wait)
    read_stdout(p)  
    write(p, "echo pipetestcase | cat")
    output = read_stdout(p)
    if "pipetestcase" in output and len(output) < length_cutoff:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

def _test_bg_cat_immediate_exit(comment_file_path, student_dir, command_wait=0.05):
    start_test(comment_file_path, "Testing 'cat &' exits immediately")

    try:
        p = start('./mysh')
        write(p,"cat &")
        sleep(command_wait)
        output1 = read_stdout(p) # job message
        write(p,"") # to trigger catch_children()
        output1 = read_stdout(p)
        if "[1]+ Done" not in output1 or "cat" not in output1:
            finish(comment_file_path, "NOT OK") 
            return
        finish(comment_file_path, "OK") 
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def test_bg_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Sample bg runs")
  start_with_timeout(_test_simple_bg, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_responsive_shell, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_multiple_bg, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Sample ps runs")
  start_with_timeout(_test_single_ps, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_multiple_ps, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Background jobs finish correctly")
  start_with_timeout(_test_bg_completes, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_bg_terminates, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)
  
  start_suite(comment_file_path, "bg edge cases")
  start_with_timeout(_test_count_reset, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_exceed_limits, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "bg integrations tests")
  start_with_timeout(_test_bg_pipes, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "bg stdin tests")
  start_with_timeout(_test_bg_cat_immediate_exit, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)
