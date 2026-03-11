system ssh client admin-state
-----------------------------

**Minimum user role:** operator

SSH client configuration enables to set accessibility from the NCR to a remote device via SSH.

The SSH client functionality is disabled by default. To enable or disable it:

**Command syntax: client admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ssh

**Note**

- Changing the client admin-state to "disabled" will immediately terminate any active session.

.. - no command returns the state to default.

	- Active sessions are immediately disconnected upon configuration of "disable".

**Parameter table**

+-------------+------------------------------------------------------+----------+---------+
| Parameter   | Description                                          | Range    | Default |
+=============+======================================================+==========+=========+
| admin-state | Configure the state of the SSH client on the system. | Enabled  | Enabled |
|             |                                                      | Disabled |         |
+-------------+------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ssh
	dnRouter(cfg-system-ssh)# client admin-state enabled
	dnRouter(cfg-system-ssh)# client admin-state disabled
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ssh)# no client admin-state

.. **Help line:** Enabled/Disabled ssh client functionality on system.

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 5.1.0   | Command introduced                      |
+---------+-----------------------------------------+
| 6.0     | Added admin-state to the command syntax |
|         | Applied new hierarchy                   |
+---------+-----------------------------------------+


