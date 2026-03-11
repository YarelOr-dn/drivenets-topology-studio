system high-availability
------------------------

**Minimum user role:** operator

High-availability configuration control system behavior upon software failure.

To enter the high-availability configuration level:

**Command syntax: high-availability**

**Command mode:** config

**Hierarchies**

- system

**Note**


**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)#



**Removing Configuration**

To remove all high-availability configuration and return to default high-availability behavior:
::

	dnRouter(cfg-system)# no high-availability


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
