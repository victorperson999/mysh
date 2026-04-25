from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import shutil
import pty
import sys
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import *
import random 

def execute_echo_test(comment_file_path, message, expected):
  limit = len(expected) + 10  
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    command = "echo {}".format(message)
    write_no_stdout_flush(p, command)
    output = read_stdout(p)
    if expected in output and len(expected) < limit:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_character(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo of one character displays correctly")
  sent = "a"
  expected = "a"
  execute_echo_test(comment_file_path, sent, expected)

def _test_simple(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo of simple message displays correctly")
  sent = "test1"
  expected = "test1"
  execute_echo_test(comment_file_path, sent, expected)

def _test_simple2(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo of simple message displays correctly v3")
  sent = "another simple message"
  expected = "another simple message"
  execute_echo_test(comment_file_path, sent, expected)

def _test_simple3(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo of simple message displays correctly v3")
  sent = "@#*%*(*#(%**)*^%*#@"
  expected = "@#*%*(*#(%**)*^%*#@"
  execute_echo_test(comment_file_path, sent, expected)

def _test_no_errors(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo of simple message does not show errors")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    command = "echo normal message"
    write_no_stdout_flush(p, command)
    output = read_stderr(p)    # Should timeout, since no errors should be displayed
    finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_mixed(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo of mixed message displays correctly")
  sent = "mixed echo test Smysh"
  expected = "mixed echo test Smysh"
  execute_echo_test(comment_file_path, sent, expected)

def _test_quotes(comment_file_path, student_dir):
  start_test(comment_file_path, "echo with quotes has no special meaning")
  sent = "\"hello world\""
  expected = "\"hello world\""
  execute_echo_test(comment_file_path, sent, expected)

def _test_extra_spaces(comment_file_path, student_dir):
  start_test(comment_file_path, "echo ignores extra spaces")
  sent = "hello     world"
  expected = "hello world"
  execute_echo_test(comment_file_path, sent, expected)

def _test_two_echo(comment_file_path, student_dir):
  start_test(comment_file_path, "Two echo commands display correctly")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    message1 = "message1"
    message2 = "message2"
    command = "echo {}".format(message1)
    write_no_stdout_flush(p, command)
    output1 = read_stdout(p)
    command = "echo {}".format(message2)
    write_no_stdout_flush(p, command)
    output2 = read_stdout(p)
    if message1 in output1 and message2 in output2:
      finish_process(comment_file_path, "OK", p)  
    else:
      finish_process(comment_file_path, "NOT OK", p)  
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_two_no_stderr(comment_file_path, student_dir):
  start_test(comment_file_path, "Two echo commands do not show error")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    message1 = "message1"
    message2 = "message2"
    command = "echo {}".format(message1)
    write_no_stdout_flush(p, command)
    command = "echo {}".format(message2)
    write_no_stdout_flush(p, command)
    err = read_stderr(p)
    finish_process(comment_file_path, f"NOT OK")
  except Exception as e:
    finish_process(comment_file_path, "NOT OK")

def _test_mixed_error(comment_file_path, student_dir, command_wait=TESTS_TIMEOUT_M1/10):
  start_test(comment_file_path, "Echo commands work while other commands error")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    command1 = "echo test message"
    command2 = "b" * 20
    command3 = "echo another test message"
    write_no_stdout_flush(p, command1)
    sleep(command_wait)
    output1 = read_stdout(p)
    if "test message" not in output1:
      finish_process(comment_file_path, "NOT OK", p)  
      return 
    
    write_no_stdout_flush(p, command2)
    sleep(command_wait)
    output2 = read_stderr(p)
    if "ERROR: " not in output2:
      finish_process(comment_file_path, "NOT OK", p)  
      return 
    
    write_no_stdout_flush(p, command3)
    sleep(command_wait)
    output3 = read_stdout(p)
    if "another test message" not in output3:
      finish_process(comment_file_path, "NOT OK", p)  
      return

    finish_process(comment_file_path, "OK", p)  
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def test_echo_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Echo Simple Messages")
  start_with_timeout(_test_character, comment_file_path)
  start_with_timeout(_test_simple, comment_file_path)
  start_with_timeout(_test_simple2, comment_file_path)
  start_with_timeout(_test_simple3, comment_file_path)
  start_with_timeout(_test_no_errors, comment_file_path, timeoutFeedback="OK\n")
  end_suite(comment_file_path)
  start_suite(comment_file_path, "Echo Special Characters")
  start_with_timeout(_test_mixed, comment_file_path)
  start_with_timeout(_test_quotes, comment_file_path)
  start_with_timeout(_test_extra_spaces, comment_file_path)
  end_suite(comment_file_path)
  start_suite(comment_file_path, "Multiple Commands")
  start_with_timeout(_test_two_echo, comment_file_path)
  start_with_timeout(_test_two_no_stderr, comment_file_path, timeoutFeedback="OK\n")
  start_with_timeout(_test_mixed_error, comment_file_path)
  end_suite(comment_file_path)
  
