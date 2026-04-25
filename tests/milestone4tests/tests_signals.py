"""
Test that when a CTRL+C is sent to a process the process does not terminate.
"""
from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
import signal
from tests_helpers import *

def _test_survive(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "A shell can survive a SIGINT signal")

  try:
    p = start('./mysh')
    sleep(command_wait)
    os.kill(p.pid, signal.SIGINT)
    sleep(command_wait)
    read_stdout(p)   # The CTRL+C line should be mysh$ (flushed due to ^C)
    write(p, "echo hi")
    sleep(command_wait)
    output = read_stdout(p)
    if "hi" in output:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

def _test_builtin_terminate(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Builtin command terminates on a SIGINT signal, returning control to shell")

  try:
    p = start('./mysh')
    sleep(command_wait)
    write(p, "cat")
    sleep(command_wait)
    write(p, "hi")
    sleep(command_wait)
    output1 = read_stdout(p)
    if "hi" not in output1:
      finish_process(comment_file_path, f"NOT OK", p)
      return
    os.kill(p.pid, signal.SIGINT)
    read_stdout(p)   # The CTRL+C line should be mysh$ (flushed due to ^C)
    sleep(command_wait)
    write(p, "echo hello")
    sleep(command_wait)
    output = read_stdout(p)
    if "hello" in output:
      finish(comment_file_path, "OK")
    else:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

def _test_terminate(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "A shell can terminate another shell")

  try:
    p = start('./mysh')
    p2 = start('./mysh')

    write(p, "kill {}".format(p2.pid))
    sleep(command_wait)
    write(p2, "echo hi")
    finish(comment_file_path, "NOT OK")
  except Exception as e:
    # The pipe should be broken, since p2 was killed. 
    finish(comment_file_path, "OK")


def _test_terminate_signal(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "A shell can terminate another shell by sending a signal")
  try:
    p = start('./mysh')
    p2 = start('./mysh')

    write(p, "kill {} 15".format(p2.pid))
    sleep(command_wait)
    write(p2, "echo hi")
    finish(comment_file_path, "NOT OK")
  except Exception as e:
    # The pipe should be broken, since p2 was killed. 
    finish(comment_file_path, "OK")

def _test_invalid_pid(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "kill reports an error if the pid is invalid")
  try:
    p = start('./mysh')
    write(p, "kill 1122345566")
    sleep(command_wait)

    output = read_stderr(p)
    if "ERROR: The process does not exist" not in output:
      finish(comment_file_path, "NOT OK")
      return 
    
    finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_invalid_signal(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Program reports an error if the signal is invalid")
  try:
    p = start('./mysh')

    write(p, "kill {} 191".format(p.pid))
    sleep(command_wait)

    output = read_stderr(p)
    if "ERROR: Invalid signal specified" not in output:
      finish(comment_file_path, "NOT OK")
      return 
    
    finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_terminate_variable(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "A shell can terminate another shell while accepting variables")
  try:
    p = start('./mysh')
    p2 = start('./mysh')

    write(p, "signal=15")
    sleep(command_wait)
    write(p, "kill {} $signal".format(p2.pid))
    sleep(command_wait)
    write(p2, "echo hi")
    finish(comment_file_path, "NOT OK")
  except Exception as e:
    # The pipe should be broken, since p2 was killed. 
    finish(comment_file_path, "OK")




def test_signals_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Shell survives a control C")
  start_with_timeout(_test_survive, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Sample kill runs")
  start_with_timeout(_test_terminate, comment_file_path, student_dir)
  start_with_timeout(_test_terminate_signal, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Kill error handling")
  start_with_timeout(_test_invalid_pid, comment_file_path, student_dir)
  start_with_timeout(_test_invalid_signal, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Kill Integration Tests")
  start_with_timeout(_test_terminate_variable, comment_file_path, student_dir)
  end_suite(comment_file_path)
  
  start_suite(comment_file_path, "Builtin Terminates on Ctrl C")
  start_with_timeout(_test_builtin_terminate, comment_file_path, student_dir)
  end_suite(comment_file_path)
