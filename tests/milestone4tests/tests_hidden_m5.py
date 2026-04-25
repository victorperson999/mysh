from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import *



def _test_bg_termination_counts(comment_file_path, student_dir, command_wait=0.05, length_cutoff=70):
  start_test(comment_file_path, "Background jobs terminate with correct counts after kill")

  try:
    p = start('./mysh')
    for i in range(10):  
        write(p,"sleep 943 &")
        output = read_stdout(p)   # Background process creation message
        output = output.strip('\n')
        closing_bracket = output.index("]")
        pid_start = closing_bracket + 2
        pid = int(output[pid_start:])
        write(p, "kill {}".format(pid))
        sleep(command_wait)
        write(p, "time=1000")
        sleep(command_wait)
        output = read_stdout(p)
        if not ("[1]+ Done" in output and "sleep 943" in output and len(output) < length_cutoff):
            finish(comment_file_path, "NOT OK")
            return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_bg_pipes(comment_file_path, student_dir, command_wait=0.05, length_cutoff=40):
  start_test(comment_file_path, "Pipes work correctly during background process")

  try:
    p = start('./mysh')
    write(p, "sleep 100 &")
    read_stdout(p)   # Background process creation message
    write(p, "echo catdisplaymessage | cat")
    output = read_stdout(p)
    if "catdisplaymessage" not in output or len(output) > length_cutoff:
      finish(comment_file_path, "NOT OK")  
      return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_multiple_ps_with_pipes(comment_file_path, student_dir, command_wait=0.05):
  start_test(comment_file_path, "ps command shows multiple background processes, including one with a pipe")

  try:
    p = start('./mysh')
    write(p,"sleep 30 &")
    sleep(command_wait)
    out = read_stdout(p)
    print(out)
    sleep(command_wait)
    write(p,"sleep 30 | cat &")
    sleep(command_wait)

    # clears background task output
    os.set_blocking(p.stdout.fileno(), False)
    
    while not stdout_empty(p):
      p_output = read_stdout(p)
      print(p_output)
      sleep(command_wait)
      # Should not put each process on its on line. The job is "[2] sleep 5 | cat"
      if "[3]" in p_output:
          finish(comment_file_path, "NOT OK -- too many jobs")
          return

    write(p,"ps")
    sleep(command_wait)

    ps_output = p.stdout.read().decode("utf-8").strip()
    print(ps_output)
    if "[3]" in ps_output or ps_output.count("sleep") != 2 or ps_output.count("cat") != 1:
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")



def test_milestone5_hidden_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Hidden - correct counts for background job termination")
  start_with_timeout(_test_bg_termination_counts, comment_file_path, student_dir)
  end_suite(comment_file_path)
  
  start_suite(comment_file_path, "Hidden - pipes work correctly during background process")
  start_with_timeout(_test_bg_pipes, comment_file_path, student_dir)
  start_with_timeout(_test_multiple_ps_with_pipes, comment_file_path, student_dir, timeout=10)
  end_suite(comment_file_path)
