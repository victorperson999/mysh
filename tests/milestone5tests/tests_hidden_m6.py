import signal
from subprocess import CalledProcessError, STDOUT, check_output, TimeoutExpired, Popen, PIPE, getstatusoutput
import os
import random 
import shutil
import pty
import datetime
import sys
sys.path.append("..")
from time import sleep 
import subprocess
import multiprocessing 
from tests_helpers import *
import socketserver
import socket 


def get_free_port():
    with socketserver.TCPServer(("localhost", 0), None) as s:
        free_port = s.server_address[1]
    return free_port

# Return True if the port is used, otherwise False. 
def port_running(port):
    output = getstatusoutput('lsof | grep mysh')[1]
    return str(port) in output
 

def generate_random_message():
  length = random.randint(10, 30)
  message = ""
  characters = ["a", "b", "c", "d", "e", " "]
  for i in range(length):
    message += random.choice(characters)
  return message

# Multiple clients

def _test_multi_clients(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=35):
    start_test(comment_file_path, "Hidden - Multiple clients multiple messages")
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        p3 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        sleep(command_wait)
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)
        write_no_stdout_flush(p2,"start-client {} {}".format(free_port, hostname))
        write_no_stdout_flush(p3,"start-client {} {}".format(free_port, hostname))
        sleep(command_wait)
        write_no_stdout_flush(p2, "message1")
        sleep(command_wait)
        output = ""
        while output == "":
            output = read_stdout(p)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
            sleep(command_wait)

        if "message1" not in output:
            finish(comment_file_path, "NOT OK")
            return 
        write_no_stdout_flush(p2, "message2")
        sleep(command_wait)
        output = ""
        while output == "":
            output = read_stdout(p)  
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        
        if "message2" not in output:
            finish(comment_file_path, "NOT OK")
            return 
        write_no_stdout_flush(p3, "message3")
        sleep(command_wait)
        output = ""
        while output == "":
            output = read_stdout(p)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")

        if "message3" not in output:
            finish(comment_file_path, "NOT OK")
            return 
        
        if has_memory_leaks(p):
            finish(comment_file_path, "NOT OK")
        else:
            finish(comment_file_path, "OK")
    except Exception as e:
        return "NOT OK"


# Integration Tests 

def _test_server_pipes(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=35):
    start_test(comment_file_path, "Pipe commands work through the server")
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        sleep(command_wait)
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)
        write_no_stdout_flush(p2, "send {} {} hi".format(free_port, hostname))
        sleep(command_wait)
        output = read_stdout(p)
        if "hi" not in output:
            logger("hi", output)
            finish(comment_file_path, "NOT OK")
            return 
        
        # Try using pipes 
        write_no_stdout_flush(p, "echo message | cat")
        sleep(command_wait)
        output = read_stdout(p)
        if "message" not in output:
            logger("message", output)
            finish(comment_file_path, "NOT OK")
        
        # Exhange a message again 

        write_no_stdout_flush(p2, "send {} {} nextmessage".format(free_port, hostname))
        sleep(command_wait)
        output = read_stdout(p)
        output2 = read_stdout(p)
        logger("2:", output2)
        if "nextmessage" not in output:
            logger("nextmessage", output)
            finish(comment_file_path, "NOT OK")
            return 

        finish(comment_file_path, "OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def test_close_reopen(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    start_test(comment_file_path, "Server closes and reopens correctly")
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        sleep(command_wait)
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)

        write_no_stdout_flush(p2,"send {} {} testing message".format(free_port, hostname))
        sleep(command_wait)

        output = read_stdout(p)
        if len(output) >= LENGTH_CUTOFF or "testing message" not in output:
            finish(comment_file_path, "NOT OK -- initial message not sent") 
            return
        
        write_no_stdout_flush(p,"close-server")
        sleep(command_wait)
        read_stdout(p) # empty buffer

        write_no_stdout_flush(p2,"send {} {} testing message".format(free_port, hostname))
        sleep(command_wait+0.5)

        if read_stdout(p) != '': # shouldnt get the message
            finish(comment_file_path, "NOT OK -- host doesnt close")
            return
        if "ERROR:" not in read_stderr(p2):
            finish(comment_file_path, "NOT OK -- client doesnt error when sending to closed host")
            return
        
        read_stdout(p2) # empty buffer

        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)

        write_no_stdout_flush(p2,"send {} {} testing message".format(free_port, hostname))
        sleep(command_wait)

        output = read_stdout(p)
        if len(output) >= LENGTH_CUTOFF or "testing message" not in output:
            finish(comment_file_path, "NOT OK -- message not recieved after reopenning server") 
            return

        finish(comment_file_path, "OK")

    except Exception as e:
        finish(comment_file_path, "NOT OK")
    finally:
        signal.signal(signal.SIGINT, signal.default_int_handler)



def suite_hidden_reopen_server(comment_file_path, student_dir):
    start_suite(comment_file_path, "Hidden - Reopen server")
    start_with_timeout(test_close_reopen, comment_file_path, student_dir, timeout=5)
    end_suite(comment_file_path)


def suite_hidden_multiple_clients(comment_file_path, student_dir):
    start_suite(comment_file_path, "Hidden - Multiple clients multiple messages")
    start_with_timeout(_test_multi_clients, comment_file_path, student_dir, timeout=5)
    end_suite(comment_file_path)


def suite_hidden_integration(comment_file_path, student_dir):
    start_suite(comment_file_path, "Hidden - Integration Tests")
    start_with_timeout(_test_server_pipes, comment_file_path, student_dir)
    end_suite(comment_file_path)

def test_milestone6_hidden_suite(comment_file_path, student_dir, autofail = False):
    execute_suite(suite_hidden_reopen_server, comment_file_path, student_dir, "Hidden - Reopen server", autofail)
    execute_suite(suite_hidden_multiple_clients, comment_file_path, student_dir, "Hidden - Multiple clients multiple messages", autofail)
    execute_suite(suite_hidden_integration, comment_file_path, student_dir, "Hidden - Integration Tests", autofail)
