Concatenating Commands
----------------------

**Minimum user role:** operator

You can concatenate show commands in a single command line. The concatenated commands are separated by a semicolon, as follows:

**Example**
dnRouter# show system login users


.. **Command mode:** configuration

The output will be printed sequentially according to the order of appearance in the command line. Each printed output is prefixed with a hash sign (#) indicating that the following output is for a different command:



**Example**
dnRouter# show interfaces ; show system
# show interfaces
...
# show system
...	




