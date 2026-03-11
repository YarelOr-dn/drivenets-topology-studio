system name
-----------

**Minimum user role:** operator

The system name identifies the server in the CLI prompt and elsewhere. The system name is provided automatically during deployment, but you can change the default name, as follows:

**Command syntax: name [system-name]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- The new name will appear in the prompt after commit. See Transaction Commands.
- Support the following characters: 0-9 a-z A-Z - _ .

.. - no command reverts the system name to default

**Parameter table**

+-------------+----------------------------------------------------------------------------+-------------------+----------+
| Parameter   | Description                                                                | Range             | Default  |
+=============+============================================================================+===================+==========+
| system-name | assign the system a new name. The assigned name appears in the CLI prompt. | 1..48 characters  | dnRouter |
+-------------+----------------------------------------------------------------------------+-------------------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# name MyAmazingSystem

	# after commit..


	# after commit..

	dnRouter(cfg)#


**Removing Configuration**

To revert the router-id to default:
::

	MyAmazingSystem(cfg-system)# no name

.. **Help line:** Configure system name

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy               |
+---------+-------------------------------------+
| 9.0     | Name size limited to 255 characters |
+---------+-------------------------------------+
| 16.2    | Name size limited to 24 characters  |
+---------+-------------------------------------+
| 18.0    | Name size limited to 48 characters  |
+---------+-------------------------------------+
