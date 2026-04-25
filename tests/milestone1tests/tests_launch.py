from subprocess import Popen, PIPE
from tests_helpers import *



def _test_exit(comment_file_path, student_dir):
  start_test(comment_file_path, "exit causes process to terminate with correct return code")
  p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
  stdout, stderr = p.communicate(input='exit'.encode())
  if stderr or p.returncode != 0:
      finish_process(comment_file_path, "NOT OK", p)
  else:
      finish_process(comment_file_path, "OK", p)   # Terminated successfully 
  

def _test_shell_message(comment_file_path, student_dir, timeout=TESTS_TIMEOUT_M1):
  start_test(comment_file_path, "Shell message is displayed, uses exit to test")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout = p.communicate(input='exit'.encode(), timeout=timeout)[0]
    if stdout == b"mysh$ ":
      finish_process(comment_file_path, "OK", p)  
    else:
      finish_process(comment_file_path, "NOT OK", p)
  except Exception:
    finish_process(comment_file_path, "NOT OK", p)


def test_launch_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Launch Suite")
  start_with_timeout(_test_exit, comment_file_path)
  start_with_timeout(_test_shell_message, comment_file_path)
  end_suite(comment_file_path)
