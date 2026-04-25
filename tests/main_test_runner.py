import sys

from tests_helpers import *

sys.path.append("milestone1tests/")
sys.path.append("milestone2tests/")
sys.path.append("milestone3tests/")
sys.path.append("milestone4tests/")
sys.path.append("milestone5tests/")
import time
import os
import datetime
import multiprocessing
# Milestone 1 tests
import tests_compile, tests_commands, tests_echo, tests_launch
# Milestone 2 tests
import tests_variables
# Milestone 3 tests
import tests_cat, tests_wc, tests_ls_cd
# Milestone 4 tests
import tests_builtins_pipes, tests_bash, tests_bg, tests_signals
# Milestone 5 tests 
import tests_short_client, tests_long_client, tests_additional_processes

current_dir = os.path.dirname(os.path.abspath(__file__))

student_submissions_path = os.path.dirname(os.path.abspath(__file__))+ "/../"


def _helper_cd_to_student(student_dir):
  cwd = os.getcwd()  
  os.chdir(student_dir)
  cwd = os.getcwd()  

def _helper_return_to_original_dir():
  os.chdir(current_dir) 
  cwd = os.getcwd()  

def run_milestone1_tests(comment_file_path, student_dir):
  tests_launch.test_launch_suite(comment_file_path, student_dir)
  tests_commands.test_commands_suite(comment_file_path, student_dir)
  tests_echo.test_echo_suite(comment_file_path, student_dir)

def run_milestone2_tests(comment_file_path, student_dir): 
  tests_variables.test_variables_suite(comment_file_path, student_dir)


def run_milestone3_tests(comment_file_path, student_dir): 
  tests_cat.test_cat_suite(comment_file_path, student_dir)
  tests_wc.test_wc_suite(comment_file_path, student_dir)
  tests_ls_cd.test_ls_cd_suite(comment_file_path, student_dir)


def run_milestone4_tests(comment_file_path, student_dir):
  tests_builtins_pipes.test_builtin_pipes_suite(comment_file_path, student_dir)
  tests_bash.test_bash_suite(comment_file_path, student_dir)
  tests_bg.test_bg_suite(comment_file_path, student_dir)
  tests_signals.test_signals_suite(comment_file_path, student_dir)

def run_milestone5_tests(comment_file_path, student_dir):
  autofail = tests_additional_processes.test_additional_processes_suite(comment_file_path, student_dir)
  tests_short_client.test_short_client_suite(comment_file_path, student_dir, autofail)
  tests_long_client.test_long_client_suite(comment_file_path, student_dir, autofail)

def run_tests(comment_file_path, student_dir):
  _helper_cd_to_student(student_dir)
  ret = tests_compile.test_compile_suite(comment_file_path, student_dir)
  if ret:
    run_milestone1_tests(comment_file_path, student_dir)
    run_milestone2_tests(comment_file_path, student_dir)
    run_milestone3_tests(comment_file_path, student_dir)
    run_milestone4_tests(comment_file_path, student_dir)
    run_milestone5_tests(comment_file_path, student_dir)
  
  _helper_return_to_original_dir()  
  return 0 


def summarize_student_grade(student_dir, comment_file):
  comment_file = open(student_dir + f"/FEEDBACK{student_dir.split('/')[-2]}.txt", "r")
  c = comment_file.read()
  count_pass = c.count("PASS")
  count_fail = c.count("FAIL")
  comment_file.close()


  total = count_fail + count_pass 
  return float(count_pass), total



def test_plan():
  f = []
  for (dirpath, dirnames, filenames) in os.walk(student_dir):
    f.extend(filenames)
    break
  
  # Set up grade structure
  comment_file_path = student_dir+f"/FEEDBACK{student_dir.split('/')[-2]}.txt"
  comment_file = open(comment_file_path, "w")
  comment_file.write(datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S") + "")
  comment_file.write(f"---Student: {student_dir.split('/')[-2]}\n")
  comment_file.close()
  student_point = {"total": 0}
  points = 0
  run_tests(comment_file_path, student_dir)
  points, total = summarize_student_grade(student_dir, comment_file)
  comment_file = open(student_dir + f"/FEEDBACK{student_dir.split('/')[-2]}.txt", "a")
  comment_file.write(datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S") + f"--- Test Suites Passed {points}/{total}\n")
  comment_file.write(datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S") + " FINISHED\n")
  comment_file.close()

  print(f"Student: {student_dir.split('/')[-2]} --- Test Suites Passed {points}/{total}")
  return student_point


def begin_testing(entire_class=False, student=None, student_path=None):
  global student_dir 

  if not entire_class and student:
    print("Student: {} {}".format(student, student_submissions_path+student)) 

    student_dir = student_submissions_path+student
    test_plan()

  if entire_class:
    all_students = [x[0] for x in os.walk(student_submissions_path)]
    f = []
    for (dirpath, dirnames, filenames) in os.walk(student_submissions_path):
      f.extend(dirnames)
      break
    all_students = f
    count = 0

    for s in all_students:
      print(f"\n\nTesting student: {s.split('/')[-1]} / {count}")
      begin_testing(entire_class=False, student=s.split("/")[-1])
      count += 1


if __name__ == "__main__":
  start = datetime.datetime.now()
  enable_debug()
  begin_testing(entire_class=False, student="src")

  logger("Time taken: ", datetime.datetime.now() - start)
