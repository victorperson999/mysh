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

def variable_test(comment_file_path, identifier, value, command_wait=0.05):
  """
  Test template for a single variable declaration.
  Precondition: identifier=value forms a valid variable declaration. 
  """
  length_cutoff = len("mysh $") + len(value) + 5 
  try:
    p = start('./mysh')
    write(p,"{}={}".format(identifier, value))
    sleep(command_wait)
    write(p,"echo ${}".format(identifier))
    output = read_stdout(p)
    if value not in output or len(value) > length_cutoff:
      finish(comment_file_path, "NOT OK")
      return 
    
    # Verify the shell can exit with no memory leaks. 
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")
    return 
  


def _test_access(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Declare and access a single variable")
  variable_test(comment_file_path, "x", "somevalue", command_wait)

def _test_access_v2(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Declare and access a single variable")
  variable_test(comment_file_path, "x", "anothervalue", command_wait)


# Simple variables + commands

def _test_declare(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Declare a single variable")
  try:
    p = start('./mysh')
    write(p,"x=1")
    sleep(command_wait)
    write(p,"echo samplevalue")
    output = read_stdout(p)
    if "samplevalue" not in output:
        finish(comment_file_path, "NOT OK")
        return  
  except Exception as e:
    finish(comment_file_path, "NOT OK")
    return 
  
  # Verify the shell can exit with no memory leaks. 
  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")

def _test_two_accesses(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Declare and access two variables")
  try:
    p = start('./mysh')
    write(p,"x=var1")
    sleep(command_wait)
    write(p,"y=var2")
    sleep(command_wait)
    write(p,"echo $x")
    output = read_stdout(p)
    if "var1" not in output or "var2" in output:
      finish(comment_file_path, "NOT OK")
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK")
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

# Custom variable accesses

def multiline_test(identifiers: list, values: list, command_wait=0.05):
  """
  Test template for multiline variable accesses
  Preconditions: 
  -identifiers[i]=values[i] is a valid variable declaration.
  -len(identifiers) == len(values)
  -echo $identifiers[0] $identifiers[1] $...  is valid.
  """
  try:
    p = start('./mysh')
    for i in range(len(identifiers)):
      write(p,"{}={}".format(identifiers[i], values[i]))
      sleep(command_wait)
    
    access = "echo"
    for i in range(len(identifiers)):
      access += " "
      access += "${}".format(identifiers[i])
    write(p, access)
    output = read_stdout(p)
    for value in values:
      if value not in output:
        return "NOT OK"
  except Exception as e:
    return "NOT OK"

  return "NOT OK" if has_memory_leaks(p) else "OK"

def _test_multiline_access(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Access variables in separate lines")
  result = multiline_test(["var1", "var2"], ["3", "5"])
  finish(comment_file_path, result)

def _test_multiline_access_v2(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Access variables in separate lines v2")
  result = multiline_test(["var1", "var2", "var3"], ["value1", "value2", "value3"])
  finish(comment_file_path, result)

def _test_no_spaces(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Variable declaration with spaces is not supported")
  try:
    p = start('./mysh')
    write(p,"x = var1")
    sleep(command_wait)
    output = read_stderr(p)
    # It does not matter which error message you report in this case, as long as some error is reported. 
    if "ERROR" not in output:   
      finish(comment_file_path, "NOT OK")
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK")
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")


def _test_echo_novars(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Test echo without any variable expansion")
  try:
    p = start('./mysh')
    write(p,"x=var1")
    sleep(command_wait)
    write(p,"echo x")
    output = read_stdout(p)
    if "x" not in output or "var1" in output:
      finish(comment_file_path, "NOT OK") 
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")

def _test_echo_empty_expansion(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Test echo with standalone $")
  try:
    p = start('./mysh')
    write(p,"echo y $ x")
    sleep(command_wait)
    output = read_stdout(p)

    if "y x" not in output or "y $ x" in output:
      finish(comment_file_path, "NOT OK") 
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")


def _test_echo_plain(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Non-existing variable displays as an empty string")
  try:
    p = start('./mysh')
    write(p,"echo $x")
    output = read_stdout(p).strip("mysh$ ")

    if output != "":
      finish(comment_file_path, "NOT OK") 
      return 
  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")


def _test_multiple_equals(comment_file_path, student_dir, command_wait=0.05, length_cutoff=30):
  start_test(comment_file_path, "Variables accesses separate by the first equal")
  variable_test(comment_file_path, "x", "====")

def redefine_test(identifier, value1, value2, command_wait=0.05):
  """
  Template for a simple variable re-defining test. 
  Precondition: The variable definitions are valid. 
  """
  try:
    p = start('./mysh')
    write(p,"{}={}".format(identifier, value1))
    sleep(command_wait)
    write(p,"{}={}".format(identifier, value2))
    sleep(command_wait)
    write(p,"echo ${}".format(identifier))
    output = read_stdout(p)
    if value2 not in output or value1 in output:
      return "NOT OK"
  except Exception as e:
    return "NOT OK"

  return "NOT OK" if has_memory_leaks(p) else "OK"


def _test_redefine(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Variable value is redefined appropriately")
  result = redefine_test("x", "var1", "var2")
  finish(comment_file_path, result)


def _test_redefine_v2(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Variable value is redefined appropriately v2")
  result = redefine_test("x", "var2", "var1")
  finish(comment_file_path, result)


# Advanced Tests 

def _test_access_100(comment_file_path, student_dir, command_wait=0.05, length_cutoff=30):
  start_test(comment_file_path, "Declare and access 100 variables")
  try:
    p = start('./mysh')
    failed = False 
    for i in range(100):
      random_number = randint(1, 100)
      value = "var{}".format(random_number)
      write(p,"x{}={}".format(i, value))
      # print(f"writing {i}")
      sleep(command_wait)
      write(p,"echo $x{}".format(i))

      output = read_stdout(p)
      # print(f"read {i}: {output}")
      if value not in output or len(output) > length_cutoff:
        failed = True 
    
    if failed:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 


# all variables have the format xn=varn where n is an integer of 0 through num_var_create
def variable_expansion(input_expansion, expected_output, num_var_create = 4, command_wait=0.05):
  try:
    p = start('./mysh')

    for i in range(4):
      value=f"var{i}"
      write(p,"x{}={}".format(i, value))
      sleep(command_wait)
    
    write(p,"echo {}".format(input_expansion))
    out = read_stdout(p).strip("mysh$ ")

    if out != expected_output:
      return "NOT OK"
  except Exception as e:
    return "NOT OK"

  if has_memory_leaks(p):
    return "NOT OK"
  else:
    return "OK"


def _test_variable_expansion_simple(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests for correct evaluation of variable expansions containing only intitialized variables")
  result = variable_expansion("$x0$x2 $x3 $x1", "var0var2 var3 var1")
  finish(comment_file_path, result)
  
def _test_variable_expansion_complex(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests for correct evaluation of variable expansions containing variables plus plaintext and uninitialized variables")
  result = variable_expansion("$x0$x2na$x2$x2 $x3 test $x1na test $x1$x0na", "var0var2var2 var3 test test var1")
  finish(comment_file_path, result)

def _test_builtin_cmd_expansion(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests that expanding into a builtin command works")
  try:
    p = start('./mysh')
    write(p,"cmd=echo")
    sleep(command_wait)
    write(p,"$cmd hi")
    sleep(command_wait)
    output = read_stdout(p)
    if "hi" not in output:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def _test_single_expansion_token_truncation(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests a token that expands into more than 128 chars is truncated")
  try:
    p = start('./mysh')
    s = "a" * 124
    write(p,f"x={s}")
    sleep(command_wait)
    write(p,"echo sometext$x")
    sleep(command_wait)
    output = read_stdout(p)
    if f"sometext{s}" in output or f"sometext{s[:120]}" not in output:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def _test_single_expansion_no_token_truncation(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests a token that expands into 128 chars is not truncated")
  try:
    p = start('./mysh')
    s = "a" * 124
    write(p,f"x={s}")
    sleep(command_wait)
    write(p,"echo some$x")
    sleep(command_wait)
    output = read_stdout(p)
    if f"some{s}" not in output:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK")

def _test_single_expansion_token_truncation_no_err(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests a token that expands into more than 128 chars doesn't throw an error")
  try:
    p = start('./mysh')
    s = "a" * 124
    write(p,f"x={s}")
    sleep(command_wait)
    write(p,"echo sometext$x")
    sleep(command_wait)
    err = read_stderr(p) # should timeout because an error should not be thrown
    finish_process(comment_file_path, "NOT OK") 
  except Exception as e:
    finish_process(comment_file_path, "NOT OK") 

def _test_multiple_expansion_token_truncation(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests a token that expands into more than 128 chars (from more than one expansion) is truncated")
  try:
    p = start('./mysh')
    s = "a" * 70
    t = "b" * 70
    write(p,f"x={s}")
    sleep(command_wait)
    write(p,f"y={t}")
    sleep(command_wait)
    write(p,"echo $x$y")
    sleep(command_wait)
    output = read_stdout(p)
    if f"{s}{t}" in output or f"{s}{t[:58]}" not in output:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def _test_multiple_expansion_token_truncation2(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests a token that expands into more than 128 chars (from more than one expansion) is truncated while others are not")
  try:
    p = start('./mysh')
    s = "a" * 70
    write(p,f"x={s}")
    sleep(command_wait)
    write(p,"echo $x$x $x")
    sleep(command_wait)
    output = read_stdout(p)
    if f"{s}{s}" in output or f"{s}{s[:58]} {s}" not in output:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def _test_multiple_expansion_token_truncation_complex(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "Tests truncation of multiple tokens that are longer than 128 chars")
  try:
    p = start('./mysh')
    v1 = "a" * 70
    v2 = "b" * 60
    write(p,f"x={v1}")
    sleep(command_wait)
    write(p,f"y={v2}")
    sleep(command_wait)
    write(p,"echo sometext $y text$x$x $x$y moretext")
    sleep(command_wait)
    output = read_stdout(p)
    if f"{v1}{v1}" in output or f"{v1}{v2}" in output or f"sometext {v2} text{v1}{v1[:54]} {v1}{v2[:58]} moretext" not in output:
      finish(comment_file_path, "NOT OK") 
      return 

  except Exception as e:
    finish(comment_file_path, "NOT OK") 
    return 

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK") 
  else:
    finish(comment_file_path, "OK") 

def test_variables_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Simple variables accesses")
  start_with_timeout(_test_access, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_access_v2, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_variable_expansion_simple, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_variable_expansion_complex, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Variable integration with other commands")
  start_with_timeout(_test_declare, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_two_accesses, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Custom variable accesses")
  start_with_timeout(_test_multiline_access, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_multiline_access_v2, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Echo without variables displays plain text")
  start_with_timeout(_test_echo_novars, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_echo_empty_expansion, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_echo_plain, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Variable values can be redefined")
  start_with_timeout(_test_redefine, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_redefine_v2, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Variable formatting edge cases")
  start_with_timeout(_test_multiple_equals, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_no_spaces, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Advanced tests")
  start_with_timeout(_test_access_100, comment_file_path, timeout=10)   # bigger timeout due to more commands
  end_suite(comment_file_path) 

  start_suite(comment_file_path, "Expanding into builtin commands")
  start_with_timeout(_test_builtin_cmd_expansion, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Truncating tokens")
  start_with_timeout(_test_single_expansion_token_truncation, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_single_expansion_no_token_truncation, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_single_expansion_token_truncation_no_err, comment_file_path, timeout=TESTS_TIMEOUT_M2, timeoutFeedback="OK\n")
  start_with_timeout(_test_multiple_expansion_token_truncation, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_multiple_expansion_token_truncation2, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  start_with_timeout(_test_multiple_expansion_token_truncation_complex, comment_file_path, timeout=TESTS_TIMEOUT_M2)
  end_suite(comment_file_path)

