set cli-ansi-color-disabled 
---------------------------

**Minimum user role:** viewer

By default, some of the show outputs of cli commands are displayed with colors. 

You can use this command to disable the ansi coloring in the show output of CLI commands. This functionality allows scripts that automate CLI interaction with DNOS to easily parse the returned output (the coloring in the output adds extra characters to the output, therefore occasionally it needs to be removed). It doesn't influence the coloring in the presentation of log/trace files and is set per individual session.


**Command syntax: set cli-ansi-color-disabled** 

**Command mode:** operational

**Note**


**Example**
::

	dnRouter# set cli-ansi-color-disabled


**Removing Configuration**

To return the system to the default value (coloring enabled):
::

	dnRouter# unset cli-ansi-color-disabled


.. **Help line:** Disable ansi colouring in CLI commands output

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+