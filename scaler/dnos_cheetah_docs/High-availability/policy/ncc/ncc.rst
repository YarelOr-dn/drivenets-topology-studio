system high-availability policy ncc
-----------------------------------

**Minimum user role:** operator

Defines the high-availability policy behavior for software components that reside in the DNOS NCC.
To enter the ncc configuration level:

**Command syntax: ncc**

**Command mode:** config

**Hierarchies**

- high-availability policy

.. **Note**


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)#



**Removing Configuration**

To revert all ncc high-availability policy configuration to default values:
::

	dnRouter(cfg-system-ha-policy)# no ncc


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
