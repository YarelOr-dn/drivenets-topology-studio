Entering Commands
-----------------

**Minimum user role:** operator

Some characters perform special action in the CLI. When using a special character inside a string (e.g. comment, description, name and regular expressions), enclose the string in double quotes ("string"). This will not change the meaning of the string. The quotes will appear in the "show config" output.

The CLI supported special characters are:

+-----------+---------------+------------------------------------------------------------+
| Character | Name          | Action                                                     |
+-----------+---------------+------------------------------------------------------------+
| ' '       | space         | Separates command parameters and arguments                 |
+-----------+---------------+------------------------------------------------------------+
| '|'       | pipe          | Filter, monitor, disable output paging (see Pipe Commands) |
+-----------+---------------+------------------------------------------------------------+
| '?'       | question mark | Invoke help menu (see Getting Help)                        |
+-----------+---------------+------------------------------------------------------------+
| '#'       | Hash          | Enter user comment (see Entering Remarks in Commands)      |
+-----------+---------------+------------------------------------------------------------+

**Example**
::

	dnRouter(cfg-policy-MyQoSPOlicy1-rule1)# description "real time service"
	dnRouter(cfg-rpl-cl)# rule 70 allow regex "65000:5000|_65000:3[0-9][0-9][0-9]?"	


