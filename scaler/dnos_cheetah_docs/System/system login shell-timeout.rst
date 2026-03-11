system login shell-timeout
----------------------------

**Minimum user role:** operator

The shell-timeout command sets the maximum time that a connection with the HostOS shell is allowed to be idle before it is disconnected. "Idle" refers to a session with no keyboard input from the user. The HostOS shell of the NCC/NCP/NCF may be accessed via Console port, IPMI SoL, or using the SSH protocol.

To configure a timeout for idle connections with the hostOS:

**Command syntax: shell-timeout [interval]**

**Command mode:** config

**Hierarchies**

- system 

.. **Note**

	- no command sets the values to default

	- interval=0 means no timeout (inifinite session)

	- access to the HostOS shell of NCC/NCP/NCF node can be acheived via console port, IPMI SoL or via SSH protocol. 

	- this command has no effect on the timeout for NCM sessions

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                          | Range | Default |
+===========+======================================================================================================================================+=======+=========+
| interval  | The maximum amount of time (in minutes) in which a session with the HostOS of the NCC/NCP/NCF can be idle before it is disconnected. | 0..90 | 30      |
|           | A value of 0 means no timeout (the session can be idle indefinitely).                                                                |       |         |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# shell-timeout 30
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no shell-timeout

.. **Help line:** configure maximum time allowed for connection to HostOS shell to be idle before it is disconnected. Idle is a session with no input from user via keyboard. Access to HostOS shell of NCC/NCP/NCF may be done either via SoL/Console or via SSH. 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+


