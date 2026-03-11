routing-policy extcommunity-list
--------------------------------

**Minimum user role:** operator

A community list is a user defined communities attribute list that can be used for matching or manipulating the communities attribute in updates. There are two types of community lists:

•	 Standard community list - defines the communities attribute
•	 Extended community list - defines the communities attribute string with regular expression

The standard community list is compiled into binary format and is directly compared to the BGP communities attribute in BGP updates. Therefore, the comparison is faster than in the extended community list.
You can set multiple extcoummunities in a single extcommunity-list.
To define a new extended community list:

**Command syntax: extcommunity-list [extcommunity-list-name]**

**Command mode:** config

**Hierarchies**

- routing policy

**Note**

- You cannot delete a community list that is attached to a policy.

.. validation:

.. if a user tries to remove an extcommunity while it is attached to any policy or protocol, the following error should be displayed:
   "Error: unable to remove extcommunity-list < extcommunity-list-name>. extcommunity-list is attached to policy <policy-name>".

.. **Help line:** Match by extended community list

**Parameter table**

+---------------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
|                           |                                                                                                                          |                     | Default |
| Parameter                 | Description                                                                                                              | Range               |         |
+===========================+==========================================================================================================================+=====================+=========+
|                           |                                                                                                                          |                     | \-      |
| extcommunity-list-name    | The name of the extended community-list. The name cannot contain   only numbers; it must contain at least one letter.    | 1..255 characters   |         |
+---------------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# extcommunity-list EXTCL_NAME
	dnRouter(cfg-rpl-extcl)#

**Removing Configuration**

To delete an extended community list:
::

	dnRouter(cfg-rpl)# no extcommunity-list EXTCL_NAME

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+