from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, \
    Popen, PIPE
import os
import shutil
import pty
import datetime
import sys

sys.path.append("..")
from time import sleep
import subprocess
import multiprocessing
import random

random.seed(31)

from tests_helpers import *


def reset_folder(folder_path):
    os.popen('rm -rf {}'.format(
        folder_path)).read()  # Remove the directory so we can recreate it
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
            setup_folder_structure(folder_root_path + "/" + file_name,
                                   file[file_name])
        else:
            command = "touch {}/{}".format(folder_root_path, file)
            os.popen(command)


def execute_wc_test(comment_file_path, read_file_path, read_file_relative_path,
                    max_output_length=30):
    try:
        expected_chars, expected_words, expected_newline = get_true_counts(
            read_file_path)
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "wc {}".format(read_file_relative_path))
        word_output = read_stdout(p)
        correct_word_count = len(
            word_output) < max_output_length and expected_words in word_output and "word count" in word_output
        character_output = read_stdout(p)
        correct_character_count = len(
            character_output) < max_output_length and "character count" in character_output and expected_chars in character_output
        newline_output = read_stdout(p)
        correct_newline_count = len(
            newline_output) < max_output_length and expected_newline in newline_output and "newline count" in newline_output
        if correct_word_count and correct_character_count and correct_newline_count:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def get_true_counts(read_file_path):
    # Run shell wc program to obtain true expected values
    stream = os.popen('wc -l {}'.format(read_file_path))
    output = stream.read()
    output = output.strip()
    expected_newline = output.split(' ')[0]

    stream = os.popen('wc -w {}'.format(read_file_path))
    output = stream.read()
    output = output.strip()
    expected_words = output.split(' ')[0]

    stream = os.popen('wc -m {}'.format(read_file_path))
    output = stream.read()
    output = output.strip()
    expected_chars = output.split(' ')[0]

    return expected_chars, expected_words, expected_newline


def _test_arbitrary_file(comment_file_path, student_dir):
    start_test(comment_file_path, "wc on an arbitrary file")

    file_name = "testfile.txt"
    file_path = student_dir + "/" + file_name
    file_ptr = open(file_path, "w")
    possible_characters = ['a', 'b', 'c', 'word', ' ', '\n']
    for i in range(100):
        file_ptr.write(random.choice(possible_characters))

    file_ptr.close()
    execute_wc_test(comment_file_path, file_path, file_name)
    remove_file(file_path)


def generate_secret_code():
    possible_characters = "abcdefghijklmnopqrstuvwxyz123456789"
    secret_code = ""
    for i in range(random.randint(5, 15)):
        secret_code += random.choice(possible_characters)
    return secret_code

def deterministic_secret_code(seed):
    possible_characters = "abcdefghijklmnopqrstuvwxyz123456789"
    secret_code = ""
    for i in range(10):
        secret_code += possible_characters[(seed + i) % len(possible_characters)]
    return secret_code


def _test_many_zeros(comment_file_path, student_dir):
    start_test(comment_file_path, "wc on an a file with many 0s")

    file_name = "testfile.txt"
    file_path = student_dir + "/" + file_name
    file_ptr = open(file_path, "w")
    # Our solution exceeds 10 seconds after 10**8
    file_ptr.write("0" * 10 ** 5)
    file_ptr.close()

    execute_wc_test(comment_file_path, file_path, file_name)
    remove_file(file_path)


def _test_arbitrary_tree(comment_file_path, student_dir, long_cutoff=30):
    start_test(comment_file_path,
               "Recursive ls correctly gathers files from an arbitrary deep tree")
    attempts = 10
    # All 10 random trees must pass for tests to pass.

    for attempt in range(attempts):
        if _arbitrary_attempt(student_dir) == "NOT OK":
            finish(comment_file_path, "NOT OK")
            break
    else:
        finish(comment_file_path, "OK")
    remove_folder(student_dir + "/testfolder")


def _arbitrary_attempt(student_dir, long_cutoff=30):
    chosen_secrets = []

    folder_structure = [{"subdirectory": []}]
    curr_dict = folder_structure[0]
    for i in range(20):
        curr_dict["subdirectory"].append({"subdirectory": []})
        # Add secrets to the tree with a 1/10 probability.
        if random.randint(1, 10) == 5:
            secret = generate_secret_code()
            chosen_secrets.append(secret)
            curr_dict["subdirectory"].append(secret)
        curr_dict = curr_dict["subdirectory"][0]

    setup_folder_structure(student_dir + "/testfolder", folder_structure)

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls --rec testfolder")
        output_files = set()
        limit = 500
        i = 0
        while i < limit:
            line = read_stdout(p).replace('mysh$ ', '')
            if line in chosen_secrets:
                chosen_secrets.remove(line)
            if len(chosen_secrets) == 0:
                if has_memory_leaks(p):
                    return "NOT OK -- MEMORY LEAKS"
                return "OK"
            if len(line) > long_cutoff:
                logger('[arbitrary ls]', line, 'longer than', long_cutoff, 'chars')
                return f"NOT OK - ls {line} longer than {long_cutoff} chars"
            i += 1
        logger('limit exceeded', chosen_secrets)
        return "NOT OK"
    except Exception as e:
        return "NOT OK"



def _test_arbitrary_tree_deterministic(comment_file_path, student_dir, long_cutoff=30):
    start_test(comment_file_path,
               "Recursive ls correctly gathers files from an arbitrary deep tree")
    attempts = 10
    # All 10 random trees must pass for tests to pass.

    for attempt in range(attempts):
        if _deterministic_attempt(student_dir, long_cutoff, seed=attempt + 1) == "NOT OK":
            finish(comment_file_path, "NOT OK")
            break
    else:
        finish(comment_file_path, "OK")
    remove_folder(student_dir + "/testfolder")


def _deterministic_attempt(student_dir, long_cutoff=30, seed = 1):
    chosen_secrets = []

    folder_structure = [{"subdirectory": []}]
    curr_dict = folder_structure[0]
    for i in range(20):
        curr_dict["subdirectory"].append({"subdirectory": []})
        # Add secrets to the tree with a 1/10 probability.
        if i % seed == 0:
            secret = deterministic_secret_code(seed + i)
            chosen_secrets.append(secret)
            curr_dict["subdirectory"].append(secret)
        curr_dict = curr_dict["subdirectory"][0]

    setup_folder_structure(student_dir + "/testfolder", folder_structure)
    folder_string = _string_folder_structure(folder_structure)
    print("Folder structure:", folder_string)

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls --rec testfolder")
        output_files = set()
        limit = 500
        i = 0
        line_string = ""
        while i < limit:
            line = read_stdout(p).replace('mysh$ ', '')
            if line in chosen_secrets:
                chosen_secrets.remove(line)
            if len(chosen_secrets) == 0:
                if has_memory_leaks(p):
                    return "NOT OK -- MEMORY LEAKS"
                return "OK"
            if len(line) > long_cutoff:
                logger('[arbitrary ls]', line, 'longer than', long_cutoff, 'chars')
                return f"NOT OK - ls {line} longer than {long_cutoff} chars"
            i += 1
        logger('limit exceeded', chosen_secrets)
        return "NOT OK"
    except Exception as e:
        return "NOT OK"


def _string_folder_structure(folder_struct_list):
    string = ""
    # reverse for stack order
    folder_queue = [[item, 0] for item in reversed(folder_struct_list)]
    while len(folder_queue) > 0:
        next_item = folder_queue.pop()
        item = next_item[0]
        item_depth = next_item[1]
        if type(item) == dict:
            for key in item.keys():
                string += f"\n{'    ' * item_depth}{key}"
                for folder_item in item[key]:
                    folder_queue.append([folder_item, item_depth + 1])
        else:
            string += f"\n{'    ' * item_depth}{item}"
    
    return string





def _test_multiple_directories(comment_file_path, student_dir):
    start_test(comment_file_path,
               "Recursive ls captures multiple sub-directories")
    setup_folder_structure(student_dir + "/testfolder",
                           [{"subdirectory": ["innerfile"]},
                            {"subdirectory2": ["foofile"]}])

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls --rec testfolder --d 1")
        expected_output = [".", "..", "subdirectory", ".", "..", "innerfile",
                           "subdirectory2", ".", "..", "foofile"]
        expected_output_lines = len(expected_output)
        output_files = []
        for _ in range(expected_output_lines):
            line = read_stdout(p).replace('mysh$ ', '')
            output_files.append(line)

        output_files = set(output_files)
        if output_files != set(expected_output):
            finish(comment_file_path, "NOT OK")

        if has_memory_leaks(p):
            finish(comment_file_path, "NOT OK")
        else:
            finish(comment_file_path, "OK")

        remove_folder(student_dir + "/testfolder")

    except Exception as e:
        finish(comment_file_path, "NOT OK")


def _test_ls_with_bad_arguments(comment_file_path, student_dir):
    start_test(comment_file_path, "ls with bad arguments")
    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls --d --rec testfolder")
        output = read_stderr(p)
        if "ERROR:" in output:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_ls_with_bad_arguments2(comment_file_path, student_dir):
    start_test(comment_file_path, "ls with bad arguments")
    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls --d 2 --f --rec testfolder")
        output = read_stderr(p)
        if "ERROR:" in output:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")

def _test_ls_with_bad_arguments3(comment_file_path, student_dir):
    start_test(comment_file_path, "ls with bad arguments")
    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls --d 2 --rec --f")
        output = read_stderr(p)
        if "ERROR:" in output:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def _test_ls_path(student_dir, path, expected, folder_structure, command_wait=0.01):
    setup_folder_structure(student_dir + '/testfolder', folder_structure)
    p = start('./mysh')

    try:
        write_no_stdout_flush_wait(p, "cd testfolder")
        sleep(command_wait)
        write_no_stdout_flush_wait(p, f"ls {path}")
        sleep(command_wait)
        expected_output = set(expected)
        expected_output_lines = len(expected_output)
        output_files = []
        logger(1)
        for i in range(expected_output_lines):
            line = read_stdout(p).replace('mysh$ ', '')
            output_files.append(line)
        logger(2)
        output_files = set(output_files)
        if output_files != expected_output:
            logger(f"Expected: {expected_output}, got: {output_files}")
            return "NOT OK"

        logger(3)
        if has_memory_leaks(p):
            logger("Memory leak detected")
            return "NOT OK"
        else:
            return "OK"
    except Exception as e:
        logger(e)
        return "NOT OK"
    finally:
        remove_folder(student_dir + '/testfolder')


def _test_ls_grandparent_hidden(comment_file_path, student_dir,
                                command_wait=0.01):
    start_test(comment_file_path,
               "ls a grandparent directory and display the files")
    if (_test_ls_path(student_dir, 'subfolder1/subfolder2/../../',
                      ['.', '..', 'subfolder1'], [
                          {"subfolder1": [
                              {"subfolder2": ["subfile"]}]}]) == "OK"):
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")


def _test_ls_great_grandparent_hidden(comment_file_path, student_dir,
                                      command_wait=0.01):
    start_test(comment_file_path,
               "ls a great grandparent directory and display the files")
    if (_test_ls_path(student_dir,
                      './subfolder1/subfolder2/subfolder3/../../..',
                      ['.', '..', 'subfolder1'], [
                          {"subfolder1": [
                              {"subfolder2": [{
                                  "subfolder3": ["subfile"]}]}]}]) == "OK"):
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")


def _test_ls_complex_path_hidden(comment_file_path, student_dir,
                                 command_wait=0.01):
    start_test(comment_file_path,
               "ls a complex path and display the files")
    if (_test_ls_path(student_dir,
                      './subfolder1/subfolder2/../../subfolder1/./subfolder2/../../../testfolder/subfolder1/subfolder2',
                      ['.', '..', 'subfile'], [
                          {"subfolder1": [
                              {"subfolder2": ["subfile"]}]}]) == "OK"):
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")


def _test_multiple_paths_ls_hidden(comment_file_path, student_dir,
                                   command_wait=0.01):
    start_test(comment_file_path, "Multiple paths in a single ls command")
    setup_folder_structure(student_dir + "/testfolder", [
        {"subfolder1": ["file1", "file2"]}])  # A single folder with one file

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls testfolder testfolder/subfolder1")
        sleep(command_wait)
        output = read_stderr(p)
        if "Too many arguments: ls takes a single path" not in output:
            logger(f"Output: {output}, expected: 'Too many arguments: ls takes a single path'")
            finish(comment_file_path, "NOT OK")
            remove_folder(student_dir + "/testfolder")
            return
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")

    remove_folder(student_dir + "/testfolder")


def _test_multiple_paths_cd_hidden(comment_file_path, student_dir,
                                   command_wait=0.01):
    start_test(comment_file_path, "Multiple paths in a single cd command")
    setup_folder_structure(student_dir + "/testfolder", [
        {"subfolder1": ["file1", "file2"]}])  # A single folder with one file

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "cd testfolder testfolder/subfolder1")
        sleep(command_wait)
        output = read_stderr(p)
        if "Too many arguments: cd takes a single path" not in output:
            logger(f"Output: {output}, expected: 'Too many arguments: cd takes a single path'")
            finish(comment_file_path, "NOT OK")
            remove_folder(student_dir + "/testfolder")
            return
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")

    remove_folder(student_dir + "/testfolder")


def _test_multiple_paths_cat_hidden(comment_file_path, student_dir,
                                    command_wait=0.01):
    start_test(comment_file_path, "Multiple paths in a single cat command")
    setup_folder_structure(student_dir + "/testfolder", [
        {"subfolder1": ["file1", "file2"]}])  # A single folder with one file

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "cat testfolder/subfolder1/file1 testfolder/subfolder1/file2")
        sleep(command_wait)
        output = read_stderr(p)
        if "Too many arguments: cat takes a single file" not in output:
            logger(f"Output: {output}, expected: 'Too many arguments: cat takes a single file'")
            finish(comment_file_path, "NOT OK")
            remove_folder(student_dir + "/testfolder")
            return
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")

    remove_folder(student_dir + "/testfolder")


def _test_multiple_paths_wc_hidden(comment_file_path, student_dir,
                                   command_wait=0.01):
    start_test(comment_file_path, "Multiple paths in a single wc command")
    setup_folder_structure(student_dir + "/testfolder", [
        {"subfolder1": ["file1", "file2"]}])  # A single folder with one file

    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "wc testfolder/subfolder1/file1 testfolder/subfolder1/file2")
        sleep(command_wait)
        output = read_stderr(p)
        if "Too many arguments: wc takes a single file" not in output:
            logger(f"Output: {output}, expected: 'Too many arguments: wc takes a single file'")
            finish(comment_file_path, "NOT OK")
            remove_folder(student_dir + "/testfolder")
            return
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")

    remove_folder(student_dir + "/testfolder")

def _test_cd_absolute_path_hidden(comment_file_path, student_dir,
                                    command_wait=0.01):
    start_test(comment_file_path, "cd with an absolute path")
    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "cd /home/ammcourt/m3")
        sleep(command_wait)
        write_no_stdout_flush_wait(p, "ls")
        sleep(command_wait)
        expected_output = set([".", "..", "samplefile"])
        expected_output_lines = len(expected_output)
        output_files = []
        for i in range(expected_output_lines):
            line = read_stdout(p).replace('mysh$ ', '')
            output_files.append(line)

        output_files = set(output_files)
        if output_files != expected_output:
            logger(f"Expected: {expected_output}, got: {output_files}")
            finish(comment_file_path, "NOT OK")
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")

def _test_ls_absolute_path_hidden(comment_file_path, student_dir,
                                    command_wait=0.01):
    start_test(comment_file_path, "ls with an absolute path")
    try:
        p = start('./mysh')
        write_no_stdout_flush_wait(p, "ls /home/ammcourt/m3")
        sleep(command_wait)
        expected_output = set([".", "..", "samplefile"])
        expected_output_lines = len(expected_output)
        output_files = []
        for i in range(expected_output_lines):
            line = read_stdout(p).replace('mysh$ ', '')
            output_files.append(line)

        output_files = set(output_files)
        if output_files != expected_output:
            logger(f"Expected: {expected_output}, got: {output_files}")
            finish(comment_file_path, "NOT OK")
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")


def _test_check_for_system(comment_file_path, student_dir):
    start_test(comment_file_path, "Check for use of system")
    try:
        logger(student_dir)
        p = subprocess.Popen(['grep', '-rn', 'system(', student_dir],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
        sleep(0.05)
        outs, errs = p.communicate()
        if outs or errs:
            logger(f"Output: {outs}, Errors: {errs}")
            finish(comment_file_path, "NOT OK")
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK")


def test_milestone3_hidden_suite(comment_file_path, student_dir):
    start_suite(comment_file_path, "Hidden - Advanced wc tests")
    start_with_timeout(_test_arbitrary_file, comment_file_path, student_dir)
    start_with_timeout(_test_many_zeros, comment_file_path, student_dir,
                       timeout=6)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - Advanced ls tests")
    # start_with_timeout(_test_arbitrary_tree, comment_file_path, student_dir,
    #                    timeout=10)
    start_with_timeout(_test_arbitrary_tree_deterministic, comment_file_path, student_dir,
                          timeout=10)
    start_with_timeout(_test_multiple_directories, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_ls_with_bad_arguments, comment_file_path,
                       student_dir)
    start_with_timeout(_test_ls_absolute_path_hidden, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_cd_absolute_path_hidden, comment_file_path,
                          student_dir, timeout=6)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - Advanced ls path tests")
    start_with_timeout(_test_ls_grandparent_hidden, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_ls_great_grandparent_hidden, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_ls_complex_path_hidden, comment_file_path,
                       student_dir, timeout=6)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - Incorrect number of arguments")
    start_with_timeout(_test_multiple_paths_ls_hidden, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_multiple_paths_cd_hidden, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_multiple_paths_cat_hidden, comment_file_path,
                       student_dir, timeout=6)
    start_with_timeout(_test_multiple_paths_wc_hidden, comment_file_path,
                       student_dir, timeout=6)
    end_suite(comment_file_path)

    start_suite(comment_file_path, "Hidden - Check for system")
    start_with_timeout(_test_check_for_system, comment_file_path, student_dir, timeout=2)
    end_suite(comment_file_path)
