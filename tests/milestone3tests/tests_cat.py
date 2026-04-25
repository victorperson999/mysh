from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import *


def _test_no_input(comment_file_path, student_dir):
  start_test(comment_file_path, "cat without a file reports an error")
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cat")
    error1 = read_stderr(p)
    if "ERROR: No input source provided" not in error1:
      finish(comment_file_path, "NOT OK")
      return 
    if not stderr_empty(p):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")

def _test_word(comment_file_path, student_dir):
  start_test(comment_file_path, "Cat on a file that contains one word")

  one_word_file = open(student_dir + "/testfile.txt", "w")
  one_word_file.write("testword\n")
  one_word_file.close()

  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cat testfile.txt")
    output = read_stdout(p)
    if "testword" in output:
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_file(student_dir + "/testfile.txt")

def _test_multiword(comment_file_path, student_dir):
  start_test(comment_file_path, "Cat on a file that contains multiple words")

  fptr = open(student_dir + "/testfile.txt", "w")
  fptr.write("word1 word2 word3\n")
  fptr.close()

  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cat testfile.txt")
    output = read_stdout(p)
    if "word1 word2 word3" in output:
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_file(student_dir + "/testfile.txt")

def _test_multiline(comment_file_path, student_dir):
  start_test(comment_file_path, "Cat on a file that contains multiple lines")

  one_word_file = open(student_dir + "/testfile.txt", "w")
  one_word_file.write("a\nb\nc\n")
  one_word_file.close()

  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cat testfile.txt")
    output1 = read_stdout(p)
    output2 = read_stdout(p)
    output3 = read_stdout(p)
    if "a" in output1 and "b" in output2 and "c" in output3:
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_file(student_dir + "/testfile.txt")



def test_cat_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "correct cat argument setup")
  start_with_timeout(_test_word, comment_file_path, student_dir)
  # we expect the following test to fail due to m4 requirements
  #start_with_timeout(_test_no_input, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "cat correctly reads sample files")
  start_with_timeout(_test_multiword, comment_file_path, student_dir)
  start_with_timeout(_test_multiline, comment_file_path, student_dir)
  end_suite(comment_file_path)
  