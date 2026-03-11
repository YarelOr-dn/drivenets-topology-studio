interfaces ipmi-ncc
-------------------

**Minimum user role:** operator

The intelligent platform management interface (IPMI) provides out-of-band management facilities and platform monitoring capabilities (e.g. temperature, fans, power supplies, etc.).

To configure the IPMI interface for an NCC:


**Command syntax: ipmi-ncc-0/0**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the ipmi-ncc interface.


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# ipmi-ncc-0/0 
	dnRouter(cfg-if-ipmi-ncc-0/0)# 


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-if)# no ipmi-ncc-0/0 


.. **Help line:** Configure ipmi-ncc-0/0 interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+
