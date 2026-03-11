system login ipmi
-----------------

**Minimum user role:** operator

To configure login parameters (user and password) for DNOS ipmi interfaces:

**Command syntax: ipmi**

**Command mode:** config

**Hierarchies**

- system login


**Note**

- Notice the change in prompt

.. - no command sets the values to default


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no ipmi

.. **Help line:** configure login parameters for DNOS ipmi interfaces.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


