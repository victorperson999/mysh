"""
Hidden tests plan:
1. echo 65 characters should report line too long 
2. echo 64 characters echo works as expected 
"""
from subprocess import Popen, PIPE 
from tests_helpers import * 





def read_stdout_no_strip(process):
    return process.stdout.readline().decode("utf-8")

def generate_random_message():
  length = random.randint(10, 30)
  message = ""
  characters = ["a", "b", "c", "d", "e", " "]
  for i in range(length):
    message += random.choice(characters)
  return message

def execute_echo_test(comment_file_path, message, expected):
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    command = "echo {}".format(message)
    write_no_stdout_flush(p, command)
    output = read_stdout(p)
    if expected in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)


def _run_after_error_long(comment_file_path, student_dir):
   # line too long
    s_error = "a" * 124
    char_length_129 = f"echo {s_error}" 
    _execute_after_error("ERROR: input line too long", char_length_129, comment_file_path, student_dir)

def _run_after_error_unknown(comment_file_path, student_dir):
   # unknown command
    _execute_after_error("ERROR: Unknown", "echonot hello", comment_file_path, student_dir)

def _execute_after_error(input_error, input_error_text, comment_file_path, student_dir):
  start_test(comment_file_path, "Commands can be executed after an error is encountered - {}".format(input_error))
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE, bufsize=0)
    write(p, input_error_text)
    sleep(0.1)
    output_error = read_stderr(p)

    s_test = "post_error_test"
    test_char = f"echo {s_test}"
    write(p, test_char)
    sleep(0.1)
    output = read_stdout(p)

    if input_error in output_error and s_test in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)


def _test_echo_126(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo command with 126 characters is displayed correctly")
  sent = "a" * 121
  expected = "a" * 121
  execute_echo_test(comment_file_path,sent, expected)

def _test_echo_129(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo command with 129 characters triggers an error message")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    s = "a" * 124
    char_length_129 = f"echo {s}" 
    write_no_stdout_flush(p, char_length_129)
    output = read_stderr(p)
    if "ERROR: input line too long" in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_echonot(comment_file_path, student_dir):
  start_test(comment_file_path, "Invalid command given that includes a valid command as a prefix")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    write_no_stdout_flush(p, "echonot hello")
    output = read_stderr(p)
    if "ERROR: Unknown" in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_exitfound(comment_file_path, student_dir):
  start_test(comment_file_path, "Invalid command given that includes a valid command as a prefix")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    write_no_stdout_flush(p, "exitfound")
    output = read_stderr(p)
    if "ERROR: Unknown" in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_suffix_space(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo command does not print trailing spaces")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    write_no_stdout_flush(p, "echo hello ")
    output = read_stdout_no_strip(p)
    if "hello " not in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_prefix_space(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo command does not print leading spaces")
  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    write_no_stdout_flush(p, "echo   hello")
    output = read_stdout_no_strip(p)
    if "  hello" not in output:
        finish_process(comment_file_path, "OK", p)
    else:
        finish_process(comment_file_path, "NOT OK", p)
  except Exception as e:
    finish_process(comment_file_path, "NOT OK", p)

def _test_extra_spaces(comment_file_path, student_dir):
  start_test(comment_file_path, "Echo command does not print extra spaces in middle")
  sent = "b  c"
  expected = "b c"
  execute_echo_test(comment_file_path, sent, expected)

def _test_random(comment_file_path, student_dir):
  start_test(comment_file_path, "echo with a random message displays correctly")

  try:
    p = Popen(['./mysh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)

    for _ in range(10):
      sent = generate_random_message().strip()
      expected = remove_extra_spaces(sent) 

      write_no_stdout_flush(p, "echo {}".format(sent))
      if expected not in read_stdout(p):
        finish_process(comment_file_path, "NOT OK", p)
              
    finish_process(comment_file_path, "OK", p)
  
  except Exception:
    finish_process(comment_file_path, "NOT OK", p)



def test_hidden_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Hidden - execute commands after an error is encountered")
  start_with_timeout(_run_after_error_long, comment_file_path)
  start_with_timeout(_run_after_error_unknown, comment_file_path)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - echo with hidden message and near limits")
  start_with_timeout(_test_random, comment_file_path)
  start_with_timeout(_test_echo_126, comment_file_path)
  start_with_timeout(_test_echo_129, comment_file_path)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - echo does not display an extra space")
  start_with_timeout(_test_suffix_space, comment_file_path)
  start_with_timeout(_test_prefix_space, comment_file_path)
  start_with_timeout(_test_extra_spaces, comment_file_path)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Hidden - echonot")
  start_with_timeout(_test_echonot, comment_file_path)
  start_with_timeout(_test_exitfound, comment_file_path)
  end_suite(comment_file_path)
  
