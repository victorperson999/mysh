

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


def get_process_children(pid, parent_label="parent"):
    try:
        output = check_output(["pgrep", "-P", str(pid)])
        children = output.decode().strip().split("\n")
        labeled_children = [(f"{parent_label}_{i}", child) for i, child in enumerate(children)]
        return labeled_children
    except CalledProcessError:
        return []

def check_if_process_running(pid):
    try:
        output = check_output(["ps", "-p", str(pid)])
        return True
    except CalledProcessError:
        return False

def _launch_server(command_wait=0.2):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    p = start_not_blocking('./mysh')
    hostname = "127.0.0.1"
    free_port = get_free_port()
    sleep(command_wait)
    write_no_stdout_flush(p,"start-server {}".format(free_port))
    sleep(command_wait)

    processes = _get_process_list(p, "mysh_server")

    return p, free_port, hostname, processes


def _connect_client(free_port, hostname, command_wait=0.2):
    p2 = start_not_blocking('./mysh')
    sleep(command_wait)
    write_no_stdout_flush(p2,"start-client {} {}".format(free_port, hostname))
    sleep(command_wait)

    processes = _get_process_list(p2, "mysh_client")

    return p2, processes


def _get_process_list(p, parent_label="parent"):
    children = get_process_children(p.pid, parent_label)
    processes = [(parent_label, p.pid)] + children
    return processes


def _test_simple_close_clean(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, processes = _launch_server(command_wait)

        write_no_stdout_flush(p,"close-server")
        sleep(command_wait)
        write_no_stdout_flush(p,"exit")
        sleep(command_wait)
        return processes
    except Exception as e:
        return []
    
def _test_simple_close(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, processes = _launch_server(command_wait)
        
        write_no_stdout_flush(p,"exit")
        sleep(command_wait)
        return processes
    except Exception as e:
        return []

def _test_simple_client_clean(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, server_p = _launch_server(command_wait)
        p2, client_p2 = _connect_client(free_port, hostname, command_wait)
        p3, client_p3 = _connect_client(free_port, hostname, command_wait)

        write_no_stdout_flush(p2,"\0")
        sleep(command_wait)
        
        
        write_no_stdout_flush(p,"close-server")
        sleep(command_wait)

        write_no_stdout_flush(p2,"exit")
        sleep(command_wait)
        write_no_stdout_flush(p3,"exit")
        sleep(command_wait)
        write_no_stdout_flush(p,"exit")
        sleep(command_wait)
        return server_p + client_p2 + client_p3
    except Exception as e:
        return []
    

def _test_simple_client(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, server_p = _launch_server(command_wait)
        p2, client_p2 = _connect_client(free_port, hostname, command_wait)
        p3, client_p3 = _connect_client(free_port, hostname, command_wait)

        write_no_stdout_flush(p,"exit")
        sleep(command_wait)

        write_no_stdout_flush(p2,"exit")
        sleep(command_wait)
        write_no_stdout_flush(p3,"exit")
        sleep(command_wait)
        return server_p + client_p2 + client_p3
    except Exception as e:
        return []
    
def _test_client_write(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, server_p = _launch_server(command_wait)
        p2, client_p2 = _connect_client(free_port, hostname, command_wait)
        p3, client_p3 = _connect_client(free_port, hostname, command_wait)

        write_no_stdout_flush(p2, "message1")
        sleep(command_wait)
        write_no_stdout_flush(p2, "message2")
        sleep(command_wait)
        write_no_stdout_flush(p3, "message3")
        sleep(command_wait)

        write_no_stdout_flush(p2,"\0")
        sleep(command_wait)
        write_no_stdout_flush(p2,"exit")
        sleep(command_wait)

        write_no_stdout_flush(p,"exit")
        sleep(command_wait)
        write_no_stdout_flush(p3,"exit")
        sleep(command_wait)
        return server_p + client_p2 + client_p3
    except Exception as e:
        return []


def _test_client_write_server_proc(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, server_p = _launch_server(command_wait)
        p2, client_p2 = _connect_client(free_port, hostname, command_wait)
        p3, client_p3 = _connect_client(free_port, hostname, command_wait)

        write_no_stdout_flush(p2, "message1")
        sleep(command_wait)
        write_no_stdout_flush(p2, "message2")
        sleep(command_wait)
        write_no_stdout_flush(p3, "message3")
        sleep(command_wait)

        write_no_stdout_flush(p,"echo test")
        sleep(command_wait)
        write_no_stdout_flush(p,"ls")
        sleep(command_wait)

        write_no_stdout_flush(p, "send {} {} hi".format(free_port, hostname))
        sleep(command_wait)

        write_no_stdout_flush(p2,"\0")
        sleep(command_wait)
        write_no_stdout_flush(p2,"exit")
        sleep(command_wait)

        write_no_stdout_flush(p,"exit")
        sleep(command_wait)
        
        write_no_stdout_flush(p3,"exit")
        sleep(command_wait)
        return server_p + client_p2 + client_p3
    except Exception as e:
        return []



def _test_server_self_send(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    try:
        p, free_port, hostname, server_p = _launch_server(command_wait)
        p2, client_p2 = _connect_client(free_port, hostname, command_wait)
        p3, client_p3 = _connect_client(free_port, hostname, command_wait)

        write_no_stdout_flush(p2, "message1")
        sleep(command_wait)
        write_no_stdout_flush(p2, "message2")
        sleep(command_wait)
        write_no_stdout_flush(p2,"\0")
        sleep(command_wait)
        write_no_stdout_flush(p2,"exit")
        sleep(command_wait)

        write_no_stdout_flush(p3, "message3")
        sleep(command_wait)

        write_no_stdout_flush(p, "send {} {} testmessage".format(free_port, hostname))
        sleep(command_wait)
        write_no_stdout_flush(p,"exit")
        sleep(command_wait)

        write_no_stdout_flush(p3,"exit")
        sleep(command_wait)
        return server_p + client_p2 + client_p3
    except Exception as e:
        return []




def _test_processes_closed(test_body, test_message, comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    start_test(comment_file_path, test_message)
    try:
        processes = test_body(comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)

        if len(processes) == 0:
            finish(comment_file_path, "NOT OK")
            return
        
        # check if server process is still running
        for process in processes:
            if check_if_process_running(process[1]):
                finish(comment_file_path, "NOT OK -- process name:{} id:{} still running".format(process[0], process[1]))
                return

        finish(comment_file_path, "OK")

    except Exception as e:
        finish(comment_file_path, "NOT OK")
    finally:
        signal.signal(signal.SIGINT, signal.default_int_handler)


def test_simple_close_clean(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - clean simple close with close-server command"
    _test_processes_closed(_test_simple_close_clean, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)

def test_simple_close(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - simple close with exit command"
    _test_processes_closed(_test_simple_close, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)

def test_simple_client_clean(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - client connect and close with clean close-server command"
    _test_processes_closed(_test_simple_client_clean, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)

def test_simple_client(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - client connect and close with exit command"
    _test_processes_closed(_test_simple_client, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)

def test_client_write(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - client write and close"
    _test_processes_closed(_test_client_write, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)

def test_client_write_server_proc(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - client connect, execute server commands, then close"
    _test_processes_closed(_test_client_write_server_proc, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)


def test_server_self_send(comment_file_path, student_dir, command_wait=0.2, LENGTH_CUTOFF=50):
    test_message = "Additional processes - Server sends message to itself then closes"
    _test_processes_closed(_test_server_self_send, test_message, comment_file_path, student_dir, command_wait, LENGTH_CUTOFF)



def test_additional_processes_suite(comment_file_path, student_dir):
    start_suite(comment_file_path, "Tests if additional processes are left running after the server is closed")
    start_with_timeout(test_simple_close_clean, comment_file_path, student_dir, timeout=5)
    start_with_timeout(test_simple_close, comment_file_path, student_dir, timeout=5)
    start_with_timeout(test_simple_client_clean, comment_file_path, student_dir, timeout=5)
    start_with_timeout(test_simple_client, comment_file_path, student_dir, timeout=5)
    start_with_timeout(test_client_write, comment_file_path, student_dir, timeout=5)
    start_with_timeout(test_client_write_server_proc, comment_file_path, student_dir, timeout=5)
    start_with_timeout(test_server_self_send, comment_file_path, student_dir, timeout=5)
    return end_suite(comment_file_path)