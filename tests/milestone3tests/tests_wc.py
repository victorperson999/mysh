from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import * 
from random import choice 


def execute_wc_test(comment_file_path, read_file_path, read_file_relative_path,max_output_length=30):
  try:
    expected_characters, expected_words, expected_newlines = get_true_counts(read_file_path)
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"wc {}".format(read_file_relative_path))
    word_output = read_stdout(p) 
    correct_word_count = len(word_output) < max_output_length and expected_words in word_output and "word count" in word_output
    character_output = read_stdout(p)  
    correct_character_count = len(character_output) < max_output_length and "character count" in character_output and expected_characters in character_output
    newline_output = read_stdout(p) 
    correct_newline_count = len(newline_output) < max_output_length and expected_newlines in newline_output and "newline count" in newline_output
    if not correct_word_count or not correct_character_count or not correct_newline_count:
      finish(comment_file_path, "NOT OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  if has_memory_leaks(p):
    finish(comment_file_path, "NOT OK")
  else:
    finish(comment_file_path, "OK")


def get_true_counts(read_file_path):
  # Run shell wc program to obtain true expected values
  stream = os.popen('wc -l {}'.format(read_file_path))
  output = stream.read()
  output = output.strip()
  expected_newline_count = output.split(' ')[0]

  stream = os.popen('wc -w {}'.format(read_file_path))
  output = stream.read()
  output = output.strip()
  expected_word_count = output.split(' ')[0]

  stream = os.popen('wc -m {}'.format(read_file_path))
  output = stream.read()
  output = output.strip()
  expected_character_count = output.split(' ')[0]
  return expected_character_count, expected_word_count, expected_newline_count


def _test_empty(comment_file_path, student_dir):
  start_test(comment_file_path, "wc on an empty file")
  file_name = "testfile.txt"
  file_path = student_dir + "/" + file_name
  file_ptr = open(file_path, "w")
  file_ptr.close()

  execute_wc_test(comment_file_path, file_path, file_name)
  remove_file(file_path)

def _test_no_input(comment_file_path, student_dir):
  start_test(comment_file_path, "wc without a filename reports an error")
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"wc")
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


def _test_multiline(comment_file_path, student_dir):
  start_test(comment_file_path, "wc on a file that contains mutliple lines")

  file_name = "testfile.txt"
  file_path = student_dir + "/" + file_name
  file_ptr = open(file_path, "w")
  file_ptr.write("a\nb\nc\n")
  file_ptr.close()

  execute_wc_test(comment_file_path, file_path, file_name)
  remove_file(file_path)

def _test_multiword(comment_file_path, student_dir):
  start_test(comment_file_path, "wc on a file that contains mutliple words in a line")
  file_name = "testfile.txt"
  file_path = student_dir + "/" + file_name
  file_ptr = open(file_path, "w")
  file_ptr.write("word1 word2 word3 word4\n")
  file_ptr.close()

  execute_wc_test(comment_file_path, file_path, file_name)
  remove_file(file_path)

def _test_blank_lines(comment_file_path, student_dir):
  start_test(comment_file_path, "wc on a file that contains blank lines")

  file_name = "testblanks.txt"
  file_path = student_dir + "/testblanks.txt"
  file_ptr = open(file_path, "w")
  file_ptr.write("word1\n\n word2\n text \n\n")
  file_ptr.close()

  execute_wc_test(comment_file_path, file_path, file_name)
  remove_file(file_path)

def test_wc_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "correct wc argument setup")
  start_with_timeout(_test_empty, comment_file_path, student_dir)
  # we expect the following test to fail due to m4 requirements
  #start_with_timeout(_test_no_input, comment_file_path, student_dir)
  end_suite(comment_file_path)

  
  start_suite(comment_file_path, "wc reports correct counts on sample files")
  start_with_timeout(_test_multiline, comment_file_path, student_dir)
  start_with_timeout(_test_multiword, comment_file_path, student_dir)
  start_with_timeout(_test_blank_lines, comment_file_path, student_dir)
  end_suite(comment_file_path)
