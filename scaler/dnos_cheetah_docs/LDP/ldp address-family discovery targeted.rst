ldp address-family discovery targeted
-------------------------------------

**Minimum user role:** operator

To enter the LDP address-family discovery targeted configuration level:

**Command syntax: discovery targeted**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

**Note**

- Notice the change in prompt. 

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# discovery targeted
	dnRouter(cfg-ldp-afi-disc-tar)#

**Removing Configuration**

To revert to the default configuration:
::

	dnRouter(cfg-protocols-ldp-afi)# no discovery targeted

.. **Help line:** Enter discovery targeted configuration level

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.0      | Command introduced    |
+-----------+-----------------------+