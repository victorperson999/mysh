import re
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
    # print(f"Found free port: {free_port}")
    return free_port

# Return True if the port is used, otherwise False. 
def port_running(port):
    output = getstatusoutput('lsof | grep mysh')[1]
    return str(port) in output
 

def _messages_exchange_attempt(messages, command_wait=0.2, LENGTH_CUTOFF=100):
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)
        write_no_stdout_flush(p2,"start-client {} {}".format(free_port, hostname))
        sleep(command_wait)
        for message in messages:
            write_no_stdout_flush(p2,message)
            sleep(command_wait)
        for message in messages:
            output = ""
            while output == "":    
                output = read_stdout(p)   
                # Taking out the mysh$ message for this test so that any blank lines before are accepted. 
                logger("exchange", output)
                output = output.replace("mysh$ ", "")
                output = output.replace("mysh$", "")
                sleep(command_wait)
            if message not in output or len(output) >= LENGTH_CUTOFF:
                return "NOT OK"
            sleep(command_wait)
        
        return "OK"
    except Exception as e:
        return "NOT OK"


def _test_message(comment_file_path,student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
  start_test(comment_file_path, "A shell can exchange a message with another shell through start-client")
#   result = _messages_exchange_attempt(["examplemessage1"], command_wait, LENGTH_CUTOFF)
  result = _messages_exchange_attempt(["examplemessage1"], command_wait, LENGTH_CUTOFF)
  finish(comment_file_path, result)


def _test_message_v2(comment_file_path,student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
  start_test(comment_file_path, "A shell can exchange a message with another shell through start-client v2")
  result = _messages_exchange_attempt(["123456789"], command_wait, LENGTH_CUTOFF)
  finish(comment_file_path, result)


# Multiple Messages
def _test_multiple_messages(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    start_test(comment_file_path, "A client launched with start-client can send multiple messages")
    test1 = _messages_exchange_attempt(["msg1", "msg2", "msg3"], command_wait, LENGTH_CUTOFF)
    test2 = _messages_exchange_attempt(["a", "b", "c"], command_wait, LENGTH_CUTOFF)
    test3 = _messages_exchange_attempt(["3245", "572", "476", "3", "4"], command_wait, LENGTH_CUTOFF)
    if test1 == "OK" and test2 == "OK" and test3 == "OK": 
        finish(comment_file_path, "OK")
    else:
        finish(comment_file_path, "NOT OK")


# Multiple clients

def _test_multi_clients(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    start_test(comment_file_path, "Multiple clients single message")
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        p3 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
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
        if not (id1:=re.match("^client\\d+:", output)):
            finish(comment_file_path, "NOT OK -- missing client id")
            return
        
        if "message1" not in output:
            finish(comment_file_path, "NOT OK -- message missing from server")
            return
        
        # make sure all clients recieve the mssage
        output = ""
        while output == "":
            output = read_stdout(p2)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        if "message1" not in output or id1.group() not in output:
            logger("message1 missing in sending client", output)
            finish(comment_file_path, "NOT OK -- message1 missing in sending client")
            return
        output = ""
        while output == "":
            output = read_stdout(p3)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        if "message1" not in output or id1.group() not in output:
            logger("message1 missing in other client", output)
            finish(comment_file_path, "NOT OK -- message1 missing in other client")
            return

        write_no_stdout_flush(p3, "message2")
        sleep(command_wait)
        output = ""
        while output == "":
            output = read_stdout(p) 
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        if not (id2:=re.match("^client\\d+:", output)):
            finish(comment_file_path, "NOT OK -- missing client id")
            return
        if id2.group() == id1.group():
            finish(comment_file_path, "NOT OK -- same client id for two clients")
            return
        if "message2" not in output:
            finish(comment_file_path, "NOT OK -- message missing from server")
            return 
        
        # make sure all clients recieve the mssage
        output = ""
        while output == "":
            output = read_stdout(p2)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        if "message2" not in output or id2.group() not in output:
            logger("message2 missing in other client", output)
            finish(comment_file_path, "NOT OK -- message2 missing in other client")
            return
        output = ""
        while output == "":
            output = read_stdout(p3)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        if "message2" not in output or id2.group() not in output:
            logger("message2 missing in sending client", output)
            finish(comment_file_path, "NOT OK -- message2 missing in sending client")
            return
        
        finish(comment_file_path, "OK")
    except Exception as e:
        logger(e)
        finish(comment_file_path, "NOT OK -- exception")

def test_connected_command(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    start_test(comment_file_path, "Connected command")
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        p3 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)
        write_no_stdout_flush(p2,"start-client {} {}".format(free_port, hostname))
        write_no_stdout_flush(p3,"start-client {} {}".format(free_port, hostname))
        sleep(command_wait)
        write_no_stdout_flush(p2, "\\connected")
        sleep(command_wait)

        output = ""
        while output == "":
            output = read_stdout(p2)
            output = output.replace("mysh$ ", "")
            output = output.replace("mysh$", "")
        if not '2' in output:
            finish(comment_file_path, "NOT OK")
        else: 
            finish(comment_file_path, "OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def test_client_ids(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    p = start_not_blocking('./mysh')
    p2 = start_not_blocking('./mysh')
    p3 = start_not_blocking('./mysh')


def _test_client_message_limit_simple(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=128):
    start_test(comment_file_path, "Client message length limit simple")
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)
        write_no_stdout_flush(p2,"start-client {} {}".format(free_port, hostname))
        sleep(command_wait)
        long_message = "x" * (LENGTH_CUTOFF + 1)

        write_no_stdout_flush(p2, long_message)
        sleep(command_wait)

        output_err = read_stderr(p2)
        sleep(command_wait)
        
        write_no_stdout_flush(p, "exit")
        sleep(command_wait)
        write_no_stdout_flush(p2, "exit")
        sleep(command_wait)

        if "ERROR" in output_err:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK")
    except Exception as e:
        finish(comment_file_path, "NOT OK")


def _test_client_message_limit_expansion(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    start_test(comment_file_path, "Client message length limit with variable expansions")
    try:
        p = start_not_blocking('./mysh')
        p2 = start_not_blocking('./mysh')
        hostname = "127.0.0.1"
        free_port = get_free_port()
        write_no_stdout_flush(p,"start-server {}".format(free_port))
        sleep(command_wait)
        write_no_stdout_flush(p2,"x=0123456789")
        sleep(command_wait)

        write_no_stdout_flush(p2,"start-client {} {}".format(free_port, hostname))
        sleep(command_wait)
        
        long_expanded_message = "$x" * 13
        write_no_stdout_flush(p2, long_expanded_message)
        sleep(command_wait)
        output_err = read_stderr(p2)
        sleep(command_wait)
        
        write_no_stdout_flush(p, "exit")
        sleep(command_wait)
        write_no_stdout_flush(p2, "exit")
        sleep(command_wait)

        if "ERROR" in output_err:
            finish(comment_file_path, "OK")
        else:
            finish(comment_file_path, "NOT OK - No error")
    except Exception as e:
        finish(comment_file_path, "NOT OK - exception")


def _test_client_port(comment_file_path,student_dir, command_wait=0.2):
  start_test(comment_file_path, "Client reports an error when no hostname is provided")

  try:
    server = start_not_blocking('./mysh')
    free_port = get_free_port()
    hostname = "127.0.0.1"
    write_no_stdout_flush(server,"start-server {} {}".format(free_port, hostname))
    sleep(command_wait)

    client = start_not_blocking('./mysh')
    write_no_stdout_flush(client,"start-client")
    sleep(command_wait)
    output = read_stderr(client)
    sleep(command_wait)
    
    write_no_stdout_flush(server, "exit")
    sleep(command_wait)
    write_no_stdout_flush(client, "exit")
    sleep(command_wait)
    
    if "ERROR" in output:
        finish(comment_file_path, "OK")   
    else:
        finish(comment_file_path, "NOT OK")   

  except Exception as e:
    finish(comment_file_path, "NOT OK")


def _test_client_hostname(comment_file_path,student_dir, command_wait=0.2):
  start_test(comment_file_path, "Client reports an error when no hostname is provided")

  try:
    server = start_not_blocking('./mysh')
    free_port = get_free_port()
    hostname = "127.0.0.1"
    write_no_stdout_flush(server,"start-server {} {}".format(free_port, hostname))
    sleep(command_wait)

    client = start_not_blocking('./mysh')
    write_no_stdout_flush(client,"start-client {}".format(free_port))
    sleep(command_wait)
    output = read_stderr(client)
    sleep(command_wait)
    
    write_no_stdout_flush(server, "exit")
    sleep(command_wait)
    write_no_stdout_flush(client, "exit")
    sleep(command_wait)

    if "ERROR" in output:
        finish(comment_file_path, "OK")   
    else:
        finish(comment_file_path, "NOT OK")   

  except Exception as e:
    finish(comment_file_path, "NOT OK")


def suite_client_errors(comment_file_path, student_dir):
    start_suite(comment_file_path, "Client error handling")
    start_with_timeout(_test_client_port, comment_file_path, student_dir, timeout=5)
    start_with_timeout(_test_client_hostname, comment_file_path, student_dir, timeout=5)
    start_with_timeout(_test_client_message_limit_simple, comment_file_path, student_dir, timeout=5)
    start_with_timeout(_test_client_message_limit_expansion, comment_file_path, student_dir, timeout=5)
    end_suite(comment_file_path)


def suite_long_client_single_message(comment_file_path, student_dir):
    start_suite(comment_file_path, "Long client single message")
    start_with_timeout(_test_message, comment_file_path, student_dir, timeout=5)
    start_with_timeout(_test_message_v2, comment_file_path, student_dir, timeout=5)
    end_suite(comment_file_path)

def suite_long_client_multiple_messages(comment_file_path, student_dir):
    start_suite(comment_file_path, "Long client multiple messages")
    start_with_timeout(_test_multiple_messages, comment_file_path, student_dir, timeout=10)
    end_suite(comment_file_path)

def suite_long_client_multi_clients(comment_file_path, student_dir):
    start_suite(comment_file_path, "Multiple clients single message")
    start_with_timeout(_test_multi_clients, comment_file_path, student_dir, timeout=7)
    end_suite(comment_file_path)


def suite_connected_command(comment_file_path, student_dir):
    start_suite(comment_file_path, "Connected command")
    start_with_timeout(test_connected_command, comment_file_path, student_dir, timeout=7)
    end_suite(comment_file_path)


def test_long_client_suite(comment_file_path, student_dir, autofail = False):
    execute_suite(suite_long_client_single_message, comment_file_path, student_dir, "Long client single message", autofail)
    execute_suite(suite_long_client_multiple_messages, comment_file_path, student_dir, "Long client multiple messages", autofail)
    execute_suite(suite_long_client_multi_clients, comment_file_path, student_dir, "Multiple clients single message", autofail)
    execute_suite(suite_client_errors, comment_file_path, student_dir, "Client error handling", autofail)
    execute_suite(suite_connected_command, comment_file_path, student_dir, "Connected command", autofail)
 

  
  

  
