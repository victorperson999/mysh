from pathlib import Path
from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE 
import os
import shutil
import pty
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import * 


def reset_folder(folder_path):
    os.popen('rm -rf {}'.format(folder_path)).read()   # Remove the directory so we can recreate it
    os.popen('mkdir {}'.format(folder_path)).read()


def setup_folder_structure(folder_root_path: str, files: list):
    """
    Create a file structure.
    folder_root_path represents the root of the file structure. 
    files is a list of files or directories. 
    Directories have the form {name: subfiles}. Files are strings. 
    """
    reset_folder(folder_root_path)
    for file in files:
        if isinstance(file, dict):
          file_name = list(file.keys())[0]
          setup_folder_structure(folder_root_path + "/" + file_name, file[file_name])
        else:
          command = "touch {}/{}".format(folder_root_path, file) 
          os.popen(command) 


def _test_empty_folder(comment_file_path, student_dir):
  comment_file = open(comment_file_path, "a")
  name = "Create a single sub-directory, and ls into that directory:"
  current_time(comment_file)
  comment_file.write(name)
  comment_file.close()

  setup_folder_structure(student_dir + "/testfolder", [])   # A single folder
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder")
    output = read_stdout(p).replace('mysh$ ', '')
    output2 = read_stdout(p).replace('mysh$ ', '')
    output_files = set([output, output2])
    if output_files != set(['.', '..']):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_folder(student_dir + "/testfolder")

def _test_single_file(comment_file_path, student_dir):
  comment_file = open(comment_file_path, "a")
  name = "Create a single sub-directory with a single file:"
  current_time(comment_file)
  comment_file.write(name)
  comment_file.close()

  setup_folder_structure(student_dir + "/testfolder", ["subfile"])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder")
    output = read_stdout(p).replace('mysh$ ', '')
    output2 = read_stdout(p).replace('mysh$ ', '')
    output3 = read_stdout(p).replace('mysh$ ', '')
    output_files = set([output, output2, output3])
    if output_files != set([".", "..", "subfile"]):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_folder(student_dir + "/testfolder")

def _test_multiple_files(comment_file_path, student_dir):
  comment_file = open(comment_file_path, "a")
  name = "Create a single sub-directory with multiple files:"
  current_time(comment_file)
  comment_file.write(name)
  comment_file.close()

  setup_folder_structure(student_dir + "/testfolder", ["subfile1", "subfile2", "subfile3", "subfile4"])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder")
    expected_output_lines = 6 
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    output_files = set(output_files)
    if output_files != set([".", "..", "subfile1", "subfile2", "subfile3", "subfile4"]):
        finish(comment_file_path, "NOT OK")
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_folder(student_dir + "/testfolder")


def _test_ls_directory(comment_file_path, student_dir):
  start_test(comment_file_path, "ls a directory")
  setup_folder_structure(student_dir + "/testfolder", ["subfile", {"subdirectory": []}])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder")
    expected_output = set([".", "..", "subfile", "subdirectory"])
    output_files = set()
    for output in range(len(expected_output)):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.add(line)
    
    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    if output_files != expected_output:
        finish(comment_file_path, "NOT OK")

    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_folder(student_dir + "/testfolder")


def _test_single_hidden(comment_file_path, student_dir):
  title = "Test ls with one hidden file"
  folder = "testfolder"
  files_reg =  ['.', '..']
  files_hidden = [".hidden1"]

  _test_hidden(comment_file_path, student_dir, folder, files_hidden, files_reg, title)


def _test_multiple_hidden(comment_file_path, student_dir):
  title = "Test ls with multiple hidden files"
  folder = "testfolder"
  files_reg =  ['.', '..', "subfile1", "subfile2", "subfile3", "subfile4"]
  files_hidden = [".hidden1", ".hidden2", ".hidden3"]

  _test_hidden(comment_file_path, student_dir, folder, files_hidden, files_reg, title)


def _test_hidden(comment_file_path, student_dir, folder, hidden_files, reg_files, title, extra_flag =""):
  start_test(comment_file_path, title)
  folder = "testfolder"

  setup_folder_structure(student_dir + f"/{folder}", hidden_files + reg_files)   # A single folder with one file
  test1 = _test_ls(comment_file_path, folder, hidden_files + reg_files, " --a" + extra_flag)
  test2 = _test_ls(comment_file_path, folder, reg_files, extra_flag)

  if test1 and test2: 
    finish(comment_file_path, "OK")
  else:
    finish(comment_file_path, "NOT OK")


def _test_hidden_recursive(comment_file_path, student_dir):
  title = "Test ls with a showing hidden directories and folders correctly in a recursive ls"
  folder = "testfolder"
  files_reg =  ['.', '..', "file1", "file2", {"folder1": ["subfile1", "subfile2"]}, "file3"]
  files_hidden = [".hidden1", ".hidden2", {".hiddenfolder3": [".hidden4", "subfile5"]}]
  
  expected_output_all = ['.', '..', '.', '..', '.', '..', 'file1', 'file2', 'folder1', 'file3', '.hidden1', '.hidden2', 
                             '.hiddenfolder3', 'subfile1', 'subfile2', '.hidden4', 'subfile5']
  expected_output_reg = ['.', '..', '.', '..', 'file1', 'file2', 'folder1', 'file3', 'subfile1', 'subfile2']

  start_test(comment_file_path, title)
  setup_folder_structure(student_dir + f"/{folder}", files_reg + files_hidden)   # A single folder with one file
  test1 = _test_ls(comment_file_path, folder, expected_output_all, " --a" + " --d 1 --rec")
  test2 = _test_ls(comment_file_path, folder, expected_output_reg, " --d 1 --rec")

  if test1 and test2: 
    finish(comment_file_path, "OK")
  else:
    finish(comment_file_path, "NOT OK")


def _test_ls(comment_file_path, folder_name, expected_output, flags = ""):
  try:
    p = start('./mysh')

    write_no_stdout_flush_wait(p,f"ls{flags} {folder_name}")
    output_files = set()
    for output in range(len(expected_output)):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.add(line)
    
    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      return False

    if output_files != set(expected_output):
        return False

    if has_memory_leaks(p):
      return False
    else:
      return True

  except Exception as e:
    return False

# Sample cd tests

def _test_cd_empty(comment_file_path, student_dir, command_wait=0.01):
  start_test(comment_file_path, "cd without a path and go to the user's home directory")
  # get a list of file names in the home dir
  home_dir_files = [file for file in os.listdir(Path.home()) if not file.startswith('.')]
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cd")
    sleep(command_wait)
    write_no_stdout_flush_wait(p,"ls")
    sleep(command_wait)
    expected_output = set([".", ".."] + home_dir_files)
    
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != expected_output:
        finish(comment_file_path, "NOT OK")
        remove_folder(student_dir + "/testfolder")
        return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  finally:
    remove_folder(student_dir + "/testfolder")


def _test_single_cd(comment_file_path, student_dir, command_wait=0.01):
  start_test(comment_file_path, "cd into a directory and display the files")
  setup_folder_structure(student_dir + "/testfolder", ["subfile"])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cd testfolder")
    sleep(command_wait)
    write_no_stdout_flush_wait(p,"ls")
    sleep(command_wait)
    expected_output = set([".", "..", "subfile"])
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)


    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output! - single", extra)
      finish(comment_file_path, "NOT OK - extra output")

    output_files = set(output_files)
    if output_files != expected_output:
        finish(comment_file_path, "NOT OK - output mismatch")
        remove_folder(student_dir + "/testfolder")
        return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK - memory leaks")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK - exception")
  
  remove_folder(student_dir + "/testfolder")

def _test_nested_cd(comment_file_path, student_dir, command_wait=0.01):
  start_test(comment_file_path, "cd into a nested directory and display the files")
  setup_folder_structure(student_dir + "/testfolder", [{"subfolder": ["subfile"]}])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"cd testfolder/subfolder")
    sleep(command_wait)
    write_no_stdout_flush_wait(p,"ls")
    sleep(command_wait)
    expected_output = set([".", "..", "subfile"])
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != expected_output:
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_folder(student_dir + "/testfolder")

# Edge cases

def _test_variable_filename(comment_file_path, student_dir, command_wait=0.01):
  comment_file = open(comment_file_path, "a")
  name = "ls a single file through a variable identifier:"
  current_time(comment_file)
  comment_file.write(name)
  comment_file.close()

  setup_folder_structure(student_dir + "/testfolder", ["subfile"])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"filename=testfolder")
    sleep(command_wait)
    write_no_stdout_flush_wait(p,"ls $filename")
    output = read_stdout(p).replace('mysh$ ', '')
    output2 = read_stdout(p).replace('mysh$ ', '')
    output3 = read_stdout(p).replace('mysh$ ', '')
    output_files = set([output, output2, output3])
    if output_files != set([".", "..", "subfile"]):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_folder(student_dir + "/testfolder")

def _test_ls_invalid(comment_file_path, student_dir):
  start_test(comment_file_path, "ls on an invalid path reports an error")
  setup_folder_structure(student_dir + "/testfolder", ["subfile", {"subdirectory": []}])   # A single folder with one file
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder/invalidpath/invalidfile.invalid")
    error1 = read_stderr(p)

    if "ERROR: Invalid path" not in error1:
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 
    
    if not stderr_empty(p):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_folder(student_dir + "/testfolder")



def _test_ls_search(comment_file_path, student_dir):
  start_test(comment_file_path, "ls correctly filters files")
  setup_folder_structure(student_dir + "/testfolder", ["subfile1", "randomfile", "randomfile2", "subfile2"])  
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder --f subfile")
    expected_output = ["subfile1", "subfile2"]
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    
    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != set(expected_output):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 

    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  
  remove_folder(student_dir + "/testfolder")


def _test_ls_search_v2(comment_file_path, student_dir):
  start_test(comment_file_path, "ls correctly filters files v2")
  setup_folder_structure(student_dir + "/testfolder", ["mysh.o", "io_helpers.c", "io_helpers.o", "io_helpers", "mysh.c"])  
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls testfolder --f helpers")
    expected_output = ["io_helpers.c", "io_helpers.o", "io_helpers"]
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")
    
    output_files = set(output_files)
    if output_files != set(expected_output):
        finish(comment_file_path, "NOT OK")
        remove_folder(student_dir + "/testfolder")  
        return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

  except Exception as e:
    finish(comment_file_path, "NOT OK")

  remove_folder(student_dir + "/testfolder")      

def _test_ls_depth0(comment_file_path, student_dir):
  start_test(comment_file_path, "Recursive ls with depth 0 does not capture inner files")
  setup_folder_structure(student_dir + "/testfolder", [{"subdirectory": ["innerfile"]} ])  
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls --rec testfolder --d 0")
    expected_output = ["subdirectory", ".", ".."]
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != set(expected_output):
        logger("Recursive ls test output files dont match expected. Expected: ", expected_output, " Got:", output_files)
        finish(comment_file_path, "NOT OK")

    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

    remove_folder(student_dir + "/testfolder")    
  except Exception as e:
    logger(e)
    finish(comment_file_path, "NOT OK")


def _test_ls_alternate_order(comment_file_path, student_dir):
  start_test(comment_file_path, "Recursive ls supports --d argument before --rec")
  setup_folder_structure(student_dir + "/testfolder", [{"subdirectory": ["innerfile"]} ])  
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls --d 0 --rec testfolder ")
    expected_output = ["subdirectory", ".", ".."]
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    
    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != set(expected_output):
        logger("[--d before --rec] Got: ", output_files, "Expected:", expected_output)
        finish(comment_file_path, "NOT OK")
      
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

    remove_folder(student_dir + "/testfolder")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")
  

def _test_ls_depth1(comment_file_path, student_dir):
  start_test(comment_file_path, "Recursive ls with depth 1 captures inner files")
  setup_folder_structure(student_dir + "/testfolder", [{"subdirectory": ["innerfile"]} ])  
  
  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls --rec testfolder --d 1")
    expected_output = ["subdirectory", ".", "..", "innerfile", ".", ".."]
    expected_output_lines = len(expected_output)
    output_files = []
    for _ in range(expected_output_lines):
        line = read_stdout(p).replace('mysh$ ', '')
        output_files.append(line)

    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != set(expected_output):
        logger("[1 depth ls] Expected:", expected_output, "Got: ", output_files)
        finish(comment_file_path, "NOT OK")
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

    remove_folder(student_dir + "/testfolder")
    
  except Exception as e:
    finish(comment_file_path, "NOT OK")

  
# Advanced tests 

def _test_deep_tree(comment_file_path, student_dir, long_cutoff=30):
  start_test(comment_file_path, "Recursive ls correctly gathers a file from a deep tree")
  folder_structure = [{"subdirectory": []}]
  
  curr_dict = folder_structure[0]
  for i in range(100):
    curr_dict["subdirectory"].append({"subdirectory": []})
    curr_dict = curr_dict["subdirectory"][0]

  secret_code = "qv5367_secret"
  curr_dict["subdirectory"].append(secret_code)
  setup_folder_structure(student_dir + "/testfolder", folder_structure) 

  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls --rec testfolder --d 101")
    output_files = set()
    limit = 500 
    i = 0 
    while i < limit:
      line = read_stdout(p).replace('mysh$ ', '')
      if secret_code in line:
        break   
      
      if len(line) > long_cutoff:
        finish(comment_file_path, "NOT OK")
        remove_folder(student_dir + "/testfolder")
        return  
      i += 1 
    else:    # Loop did not break
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 

    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")

    remove_folder(student_dir + "/testfolder")

  except Exception as e:
    finish(comment_file_path, "NOT OK")
  

def _test_recursive_search(comment_file_path, student_dir):
  start_test(comment_file_path, "Recursive ls correctly searches files in sub-directories")
  folder_structure = [{"subdirectory1": ["quercusfile"]}, {"subdirectory2": ["randomfile"]}]
  setup_folder_structure(student_dir + "/testfolder", folder_structure)

  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,"ls --f quercus --rec testfolder --d 2")
    output = read_stdout(p)
    if "quercusfile" not in output:
      finish(comment_file_path, "NOT OK")
      return 
    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_nested_dots(comment_file_path, student_dir):
  # test ./subdir/subdir/...
  folder_structure = [{"subdir1": [{"subdir2": ["file4", {"subdir3": []}]}, "file3"]}, "file1", "file2"]
  setup_folder_structure(student_dir + "/testfolder", folder_structure)
  expected_output = set([".", "..", "subdir2", "file2", "file1"])
  folder = "./subdir1/subdir2/subdir3/.../../"

  _test_ls(comment_file_path, folder, expected_output, flags = "")


def _test_dots_at_len(comment_file_path, student_dir, dot_num, full_path, max_dir, base_expected):
  start_test(comment_file_path, f"ls with varying number of dots {dot_num} in deep folder structure")

  try:
    p = start('./mysh')
    write_no_stdout_flush_wait(p,f"cd {full_path}")

    if not stderr_empty(p):
      finish(comment_file_path, "NOT OK")
      return

    input_dots = "." * dot_num
    write_no_stdout_flush_wait(p,f"ls {input_dots}")

    expected_output_lines = base_expected + [f"sd{max_dir - dot_num + 1}"]
    output_files = []

    for _ in range(len(expected_output_lines)):
      line = read_stdout(p).replace('mysh$ ', '')
      output_files.append(line)

    if not stderr_empty(p):
      finish(comment_file_path, "NOT OK")
      return

    if (extra:=read_stdout(p).strip()) != 'mysh$' or extra == '':
      logger("Too much output!", extra)
      finish(comment_file_path, "NOT OK")

    output_files = set(output_files)
    if output_files != set(expected_output_lines):
      finish(comment_file_path, "NOT OK")
      remove_folder(student_dir + "/testfolder")
      return 

    
    if has_memory_leaks(p):
      finish(comment_file_path, "NOT OK")
    else:
      finish(comment_file_path, "OK")
  except Exception as e:
    finish(comment_file_path, "NOT OK")




def _test_arbitrary_dots(comment_file_path, student_dir):
  folder_structure = [{"sd1": []}]
  curr_dict = folder_structure[0]
  full_path = "./testfolder/sd1"
  max_dir = 10
  dots = list(range(2, max_dir - 2))
  
  for i in range(2, max_dir):
      curr_dict[f"sd{i - 1}"].append({f"sd{i}": []})
      curr_dict = curr_dict[f"sd{i - 1}"][0]
      full_path += "/sd" + str(i)
  base_expected = ['.', ".."]
  setup_folder_structure(student_dir + "/testfolder", folder_structure)

  # this is a bit slow, but is safer than trying to write in a loop due to timeouts and buffer deadlocks
  for dot_num in dots:
    _test_dots_at_len(comment_file_path, student_dir, dot_num, full_path, max_dir, base_expected)

  remove_folder(student_dir + "/testfolder")


def test_ls_cd_suite(comment_file_path, student_dir):
  start_suite(comment_file_path, "Sample ls runs")
  start_with_timeout(_test_single_file, comment_file_path, student_dir)
  start_with_timeout(_test_multiple_files, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_ls_directory, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Sample cd runs")
  start_with_timeout(_test_cd_empty, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_single_cd, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_nested_cd, comment_file_path, student_dir, timeout=8)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "ls error handling")
  start_with_timeout(_test_ls_invalid, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)
  
  start_suite(comment_file_path, "ls handles edge cases correctly")
  start_with_timeout(_test_variable_filename, comment_file_path, student_dir)
  start_with_timeout(_test_empty_folder, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "ls filters files correctly")
  start_with_timeout(_test_ls_search, comment_file_path, student_dir)
  start_with_timeout(_test_ls_search_v2, comment_file_path, student_dir)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "ls --a shows hidden files correctly")
  start_with_timeout(_test_single_hidden, comment_file_path, student_dir)
  start_with_timeout(_test_multiple_hidden, comment_file_path, student_dir)
  start_with_timeout(_test_hidden_recursive, comment_file_path, student_dir)
  end_suite(comment_file_path)


  start_suite(comment_file_path, "ls can handle an arbitrary number of dots")
  start_with_timeout(_test_nested_dots, comment_file_path, student_dir)
  start_with_timeout(_test_arbitrary_dots, comment_file_path, student_dir, timeout=10)
  end_suite(comment_file_path)

  start_suite(comment_file_path, "Recursive ls displays files correctly")
  start_with_timeout(_test_ls_depth0, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_ls_depth1, comment_file_path, student_dir, timeout=6)
  start_with_timeout(_test_ls_alternate_order, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)


  start_suite(comment_file_path, "Advanced Tests")
  # start_with_timeout(_test_deep_tree, comment_file_path, student_dir, timeout=3)
  start_with_timeout(_test_recursive_search, comment_file_path, student_dir, timeout=6)
  end_suite(comment_file_path)

