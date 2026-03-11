set logging terminal 
---------------------

**Minimum user role:** viewer

To send non-persistent system-events to the terminal (console or ssh):

**Command syntax: set logging terminal**

**Command mode:** operational

**Example**
::

	dnRouter# 
	dnRouter# set logging terminal

**Removing Configuration**

To stop sending the events to the terminal:
::

	dnRouter# unset logging terminal


.. **Help line:** Set non persistant system-events messages to the terminal (console or ssh)

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+