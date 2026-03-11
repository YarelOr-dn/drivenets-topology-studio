protocols mpls
--------------

**Minimum user role:** operator

To configure MPLS, enter MPLS configuration mode:

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- Notice the change in the prompt from dnRouter(cfg-protocols)# to dnRouter(cfg-protocols-mpls)# 

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)#

**Removing Configuration**

To remove the MPLS protocol configuration:
::

	dnRouter(cfg-protocols)# no mpls	
	

.. **Help line:** configure mpls protocol

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+