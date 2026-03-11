interfaces ipmi-ncf
-------------------

**Minimum user role:** operator

The intelligent platform management interface (IPMI) provides out-of-band management facilities and platform monitoring capabilities (e.g. temperature, fans, power supplies, etc.).

To configure the IPMI interface for an NCF:

**Command syntax: ipmi-ncf-0/0**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the ipmi-ncf interface.


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# ipmi-ncf-0/0 
	dnRouter(cfg-if-ipmi-ncf-0/0)# 


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-if)# no ipmi-ncf-0/0 


.. **Help line:** configure ipmi-ncf-0/0 interface

**Command History**

+-------------+----------------------------------------------------+
|             |                                                    |
| Release     | Modification                                       |
+=============+====================================================+
|             |                                                    |
| 10.0        | Command introduced                                 |
+-------------+----------------------------------------------------+
|             |                                                    |
| 11.0        | Added support for IPMI interface on NCP and NCF    |
+-------------+----------------------------------------------------+
