set cli-terminal-length 
-----------------------

**Minimum user role:** viewer

You can set the amount of lines that will be displayed before the "more" option is shown, per cli session. In order to completely disable pagination (equivalent to "no-more" pipe), set 0 for terminal-length.

**Command syntax: set cli-terminal-length [terminal-length]** 

**Command mode:** operational

**Note**

- If the terminal-length is set with N number of lines the 'no more' command will take precedence over the number of lines N.

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------+------------+-------------+
|                    |                                                                                             |            |             |
| Parameter          | Description                                                                                 | Range      | Default     |
+====================+=============================================================================================+============+=============+
|                    |                                                                                             |            |             |
| terminal-length    | Pagination - The number of lines to display per   cli session, before the 'more' option.    | 0..1023    | \-          |
+--------------------+---------------------------------------------------------------------------------------------+------------+-------------+

**Example**

To set the number of lines:
::

	dnRouter# set cli-terminal-length 200



**Removing Configuration**

To disable pagination:
::

	dnRouter# set cli-terminal-length 0

To remove the cli-terminal-length setting for the session:
::

	dnRouter# unset cli-terminal-length

.. **Help line:** Set the amount of lines that will be displayed before "more" option will be shown

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.2        | Command introduced    |
+-------------+-----------------------+