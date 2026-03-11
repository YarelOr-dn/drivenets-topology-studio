protocols ldp
-------------

**Minimum user role:** operator

To start the process, enter LDP configuration hierarchy using the following command:

**Command syntax: protocols ldp**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- You can only configure LDP for the default VRF.

- Notice the change in prompt. 

.. - After command is set, enter ldp configuration hierarchy.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)#

**Removing Configuration**

To remove the LDP protocol configuration:
::

	dnRouter(cfg-protocols)# no protocols ldp

.. **Help line:** Starts a LDP process

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+