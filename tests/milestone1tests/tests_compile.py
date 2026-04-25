from subprocess import CalledProcessError, STDOUT, check_output
import datetime

from tests_helpers import TESTS_TIMEOUT_M1

def current_time(comment_file):
  comment_file.write(datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S") + "----")


def _test_compiles(student_dir, comment_file):
  name = "Code compiles:"
  current_time(comment_file)
  comment_file.write(name)
 
  try:
    output = check_output(["rm", "*.o mysh"], stderr=STDOUT, timeout=TESTS_TIMEOUT_M1) 
  except CalledProcessError:
    pass    # No .o files, ignore errors
  
  try:
    output = check_output(["make", "clean"], stderr=STDOUT, timeout=TESTS_TIMEOUT_M1) 
  except CalledProcessError:
    pass   # Nothing to clean, ignore errors

  try:
    output = check_output(["make", "-n"], stderr=STDOUT, timeout=TESTS_TIMEOUT_M1) 

    if not (b'Wall' in output and b'Werror' in output and b'Wextra' in output and \
       b'fsanitize' in output and b'address' in output):
      comment_file.write("FAIL\n")
      return False

    output = check_output(["make"], stderr=STDOUT, timeout=TESTS_TIMEOUT_M1)
    comment_file.write("PASS\n")
    return True
  except CalledProcessError:
    pass
  comment_file.write("FAIL\n")
  return False  


def test_compile_suite(comment_file_path, student_dir):
  comment_file = open(comment_file_path, "a")
  ret = _test_compiles(student_dir, comment_file)
  return ret 
