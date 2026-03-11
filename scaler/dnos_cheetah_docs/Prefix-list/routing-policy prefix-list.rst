routing-policy prefix-list
---------------------------

**Minimum user role:** operator

The prefix-list contains one or more ordered entries that are processed sequentially. To create a prefix-list and enter its configuration mode:

**Command syntax: prefix-list ipv4|ipv6 [prefix-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note:**

- Notice the change in prompt from dnRouter(cfg-rpl)#  to dnRouter(cfg-rpl-pl)#  (prefix-list configuration mode). When entering IPv6 prefix-list configuration mode, the prompt is dnRouter(cfg-rpl-pl6)#

- You cannot delete a prefix list that is being used by another policy or protocol.

..  no commands remove the prefix-list configuration for all prefix-list of specific address-family or for a specific prefix-list

.. validation:

.. if a user tries to remove a prefix-list while it is attached to any policy or protocol, the following error should be displayed:

.. "Error: unable to remove prefix-list <ip-prefix-list-name>. prefix-list is attached to policy <policy-name>".

..   or

.. "Error: unable to remove prefix-list <ip-prefix-list-name>. prefix-list is attached to protocol {BGP,OSPF,LDP} with <configuration> attachment point".

**Parameter table**

+------------------+------------------------------------+--------+---------+
| Parameter        | Description                        | Range  | Default |
+==================+====================================+========+=========+
| prefix-list-name | Provide a name for the prefix list | String | \-      |
|                  |                                    | 1..255 |         |
+------------------+------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv4 PL_MARTIANS
	dnRouter(cfg-rpl-pl)#

	dnRouter(cfg-rpl)# prefix-list ipv6 PL_MARTIANS
	dnRouter(cfg-rpl-pl6)#


.. **Help line:** Configure ip prefix-list

**Removing Configuration**

To remove the prefix-list configuration for all prefix lists of a specific address-family:
::

	dnRouter(cfg-rpl)# no prefix-list ipv4

To remove a specific prefix-list:
::

	dnRouter(cfg-rpl)# no prefix-list ipv6 PL_MARTIANS

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+