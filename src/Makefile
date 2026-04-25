CFLAGS = -g -Wall -Wextra -Werror -fsanitize=address,leak,object-size,bounds-strict,undefined -fsanitize-address-use-after-scope

all: mysh

mysh: mysh.o builtins.o commands.o variables.o io_helpers.o socket.o chat_helpers.o network.o
	gcc ${CFLAGS} -o $@ $^ 

%.o: %.c builtins.h commands.h variables.h io_helpers.h network.h socket.h chat_helpers.h
	gcc ${CFLAGS} -c $< 

clean:
	rm -f *.o mysh
