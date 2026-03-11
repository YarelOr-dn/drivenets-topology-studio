routing-policy as-path-list
---------------------------

**Minimum user role:** operator

When a prefix announcement passes through an AS, that AS adds its AS number to the AS-path attribute. An AS can reject an announcement for a route that it originated, or reject an announcement that contains the local AS number in its AS-path. In this way, the AS-path helps prevent looping announcements.
You can define an access-list rule for an AS-path to use with BGP.
To create an access-list rule for the AS-path and enter its configuration mode:

**Command syntax: as-path-list [as-path-list-name]**

**Command mode:** config

**Hierarchies**

- Routing-policy

**Note:**

-  no commands remove a specific the AS path list or all the entire access list.

.. INT1 validation:

.. if a user tries to remove an as-path  *-*  list while it is attached to any policy or protocol, the following error should be displayed:
..   "Error: unable to remove as-path-list < as-path-acl-name>. as-path-list is attached to policy <policy-name>". INT2

**Parameter table**

+-------------------+-------------------------------------+-------------------+---------+
| Parameter         | Description                         | Range             | Default |
+===================+=====================================+===================+=========+
| as-path-list-name | Provide a name for the as-path list | 1..255 characters | \-      |
+-------------------+-------------------------------------+-------------------+---------+

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
	dnRouter(cfg-rpl-asp)#



**Removing Configuration**

To remove the as-path rule entry:
::

		dnRouter(cfg-rpl)# no as-path-list

To remove a specific AS path list:
::

		dnRouter(cfg-rpl)# no as-path-list ASP_LOCAL

.. **Help line:** Configure as-path access-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+