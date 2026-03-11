routing-policy community-list
------------------------------

**Minimum user role:** operator

A community list is a user defined communities attribute list that can be used for matching or manipulating the communities attribute in updates. There are two types of community lists:

-	 Standard community list - defines the communities attribute
-	 Extended community list - defines the communities attribute string with regular expression

The standard community list is compiled into binary format and is directly compared to the BGP communities attribute in BGP updates. Therefore, the comparison is faster than in the extended community list.
To define a new standard community list and enter its configuration mode:

**Command syntax: community-list [community-list-name]**

**Command mode:** config

**Hierarchies**

- routing policy

**Note**

- You cannot delete a community list that is attached to a policy.

.. validation:
.. if a user tries to remove a community-list while it is attached to a policy, the following error should be displayed:
.. "Error: unable to remove community-list < community-list -name>. community-list is attached to policy <policy-name>".

**Parameter table**

+---------------------+--------------------------------+---------------+---------+
| Parameter           | Description                    | Range         | Default |
+=====================+================================+===============+=========+
| community-list-name | The name of the community-list | string        | \-      |
|                     |                                | length 1..255 |         |
+---------------------+--------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# community-list CL_NAME
	dnRouter(cfg-rpl-cl)#


**Removing Configuration**

To delete a community list:
::

	dnRouter(cfg-rpl)# no community-list CL_NAME

.. **Help line:** Configure ip community-list

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+
