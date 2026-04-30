# mysh — A Unix Shell in C

A feature-rich Unix shell implementation written in C as part of CSC209 (Software Tools and Systems Programming) at the University of Toronto. **mysh** supports substantial shell functionality including built-in commands, program execution with pipelines, background process management, signal handling, and a networked chat system.

---

## Features

### Built-in Commands
- `cd` — Change the current working directory, with `~` expansion and error reporting.
- `exit` — Gracefully terminate the shell session.
- `history` — View and re-execute previously entered commands.
- Additional filesystem utilities for directory navigation and file inspection.

### External Program Execution
- Executes external programs via `fork()` and `execvp()`, supporting both absolute and `$PATH`-resolved commands.
- Proper child process management with `waitpid()` to reap zombie processes.

### Pipelines
- Multi-stage pipelines (e.g., `ls -la | grep .c | wc -l`) implemented with `pipe()`, `dup2()`, and coordinated `fork()`/`exec()` across an arbitrary number of stages.
- Correct file descriptor plumbing ensures each stage reads from the previous stage's output and writes to the next stage's input.

### Background Processes & Job Control
- Run commands in the background with `&`.
- Asynchronous child reaping via `SIGCHLD` signal handling to prevent zombie accumulation.
- Shell remains responsive and interactive while background jobs execute.

### Signal Handling
- Custom signal handlers for `SIGINT` (Ctrl+C) and `SIGCHLD`.
- The shell process itself is protected from premature termination — signals are forwarded to foreground child processes only.
- Async-signal-safe practices followed throughout signal handler implementations.

### Networked Chat System (TCP Sockets)
- Built-in `chat` command launches a client-server chat system directly from the shell.
- **Server**: Spawned as a forked child process, listens on a configurable TCP port for incoming client connections. A pipe-based readiness signaling mechanism ensures the shell only proceeds once the server is fully bound and listening.
- **Client**: Runs directly in the shell process (not as a separate fork) to avoid stdin-sharing race conditions between the shell and client.
- **Multiplexed I/O**: Uses `select()` to simultaneously monitor stdin (user input) and the server socket (incoming messages) without blocking, enabling real-time bidirectional communication.
- Supports multiple concurrent client connections on the server side.

---

## Architecture & Design Decisions

| Decision | Rationale |
|---|---|
| **Server as a forked child with pipe-based readiness signaling** | The shell forks a child to run the server, which writes to a pipe once `bind()`/`listen()` succeed. The parent blocks on the pipe read, guaranteeing the server is ready before the client attempts to connect. |
| **Client loop in the shell process** | Running the client in the same process as the shell avoids stdin-sharing races that occur when two forked processes both try to read from the terminal. |
| **`_exit(0)` in child processes** | Child processes call `_exit()` instead of `exit()` to skip at exit handlers and bypass AddressSanitizer leak-checking overhead in forked children, avoiding false positives and unnecessary cleanup. |
| **Async-signal-safe signal handlers** | Signal handlers avoid calling non-reentrant functions (e.g., `printf`, `malloc`), using only `write()` and `waitpid()` with `WNOHANG` to safely reap children. |

---

## Build & Run

### Prerequisites
- GCC (or any C99-compatible compiler)
- POSIX-compliant OS (Linux / macOS)
- Make

### Compile
```bash
make
```

Or manually:
```bash
gcc -Wall -Werror -std=c99 -o mysh mysh.c -lm
```

### Run
```bash
./mysh
```

### Run with AddressSanitizer (for development)
```bash
gcc -Wall -Werror -std=c99 -fsanitize=address undefined -g -o mysh mysh.c -lm
./mysh
```

---

## Usage Examples

```bash
# Basic commands
mysh> ls -la
mysh> cd ~/projects
mysh> pwd

# Pipelines
mysh> cat file.txt | grep "pattern" | sort | uniq -c

# Background processes
mysh> sleep 60 &
mysh> gcc -o program program.c &

# Chat system
mysh> chat start 12345        # Start the chat server on port 12345
mysh> chat connect localhost 12345  # Connect to a running chat server
```

---

## Project Structure

```
mysh/
├── mysh.c           # Main shell loop, input parsing, command dispatch
├── builtins.c       # Built-in command implementations (cd, exit, history)
├── pipeline.c       # Pipeline construction and execution logic
├── process.c        # Process management, forking, signal handling
├── chat.c           # TCP socket server/client and select()-based I/O
├── mysh.h           # Shared type definitions and function prototypes
├── Makefile         # Build configuration
└── README.md
```

> **Note:** The actual file structure may vary — the above reflects the logical separation of concerns across the codebase.

---

- Designed every `fork()`, `pipe()`, `dup2()`, `exec()`, `bind()`, `listen()`, `accept()`, and `select()` call includes error checking and clean failure paths.

---

## Misc

- **Language:** C
- **System APIs:** POSIX (`fork`, `exec`, `pipe`, `dup2`, `waitpid`, `signal`, `select`, `socket`, `bind`, `listen`, `accept`, `connect`)
- **Tools:** GCC, Make, AddressSanitizer, Valgrind
- **Concepts:** Process control, inter-process communication, file descriptor manipulation, TCP/IP networking, multiplexed I/O, signal-safe programming

---

## Acknowledgements

Developed as coursework for **CSC209 — Software Tools and Systems Programming** at the University of Toronto Mississauga.
