interfaces mgmt0
----------------

**Minimum user role:** operator

The mgmt0 interface is a logical interface associated with the NCC. After entering the mgmt0 configuration hierarchy, proceed to configure parameters for the interface. Otherwise, default values will be used.

To configure the mgmt0 logical management interface, enter its configuration mode:

**Command syntax: mgmt0**

**Command mode:** config

**Hierarchies**

- interfaces 

**Note**

- The command is applicable to the mgmt0 interface.
- The mgmt0 IP address must differ from the mgmt-ncc address.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# mgmt0 
	dnRouter(cfg-if-mgmt0)# 


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-if)# no mgmt0 


.. **Help line:** Configures mgmt0 interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+