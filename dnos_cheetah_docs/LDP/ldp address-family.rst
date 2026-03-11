ldp address-family
-------------------

**Minimum user role:** operator

Enter address-family configuration mode:

**Command syntax: address-family [address-family-type]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- Notice the change in the prompt from dnRouter(cfg-protocols-ldp)#  to dnRouter(cfg-protocols-ldp-afi)# . You have entered the address-family configuration mode. You can proceed to configure address-family LDP parameters.

**Parameter table**

+------------------------+------------------------------------+-----------------+-------------+
|                        |                                    |                 |             |
| Parameter              | Description                        | Range           | Default     |
+========================+====================================+=================+=============+
|                        |                                    |                 |             |
| address-family-type    | Specify the address family type    | IPv4-unicast    | \-          |
+------------------------+------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)#

**Removing Configuration**

To remove the address-family configuration hierarchy:
::

	dnRouter(cfg-protocols-ldp)# no address-family ipv4-unicast

.. **Help line:** Enables the configuration of filtering policies

**Command History**

+-------------+----------------------------------------+
|             |                                        |
| Release     | Modification                           |
+=============+========================================+
|             |                                        |
| 6.0         | Command introduced                     |
+-------------+----------------------------------------+
|             |                                        |
| 13.0        | Updated range value to ipv4-unicast    |
+-------------+----------------------------------------+