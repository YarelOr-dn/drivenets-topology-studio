clear access-lists counters
---------------------------

**Minimum user role:** operator

Clearing the access-list counters resets the access-list counters to zero and deletes the counters' information from the database.

To clear the access-list counters:

**Command syntax: clear access-list counters** [interface-name] [access-list-type] [access-list-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**
 - Clear access-lists counters - clears all ACL rules on all interfaces
 - Clear access-lists counters interface x - clears all ACL rules on the specified interface
 - Clear access-lists counters interface x access-list-type - clears all rules for a specified ACL type (v4 or v6) on a specified interface
 - Clear access-lists counters interface x access-list-type access-list-name - clears all rules for a specified ACL (name+type) on a specified interface.

**Parameter table**

+---------------------+-----------------------------------------------------------------------+---------------------------------------------------+---------+
|                     |                                                                       | Range                                             | Default |
| Parameter           | Description                                                           |                                                   |         |
+=====================+=======================================================================+===================================================+=========+
|                     |                                                                       | ge<interface speed>-<A>/<B>/<C>                   |         |
| interface-name      | Clears the counters for all ACL rules on the specified interface      |                                                   |         |
|                     |                                                                       | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|         |
|                     |                                                                       |                                                   |         |
|                     |                                                                       | bundle-<bundle-id>                                |\ -      |
|                     |                                                                       |                                                   |         |
|                     |                                                                       | bundle-<bundle-id>.<sub-interface-id>             |         |
|                     |                                                                       |                                                   |         |
|                     |                                                                       | mgmt0                                             |         |
+---------------------+-----------------------------------------------------------------------+---------------------------------------------------+---------+
|                     |                                                                       |                                                   | both    |
| access-list-type    | Clears the counters for the specified ACL type                        | IPv4                                              |         |
|                     |                                                                       |                                                   |         |
|                     |                                                                       | IPv6                                              |         |
+---------------------+-----------------------------------------------------------------------+---------------------------------------------------+---------+
|                     |                                                                       |                                                   |         |
| access-list-name    | Clears the counters for the specified ACL                             | String                                            | \ -     |
+---------------------+-----------------------------------------------------------------------+---------------------------------------------------+---------+


**Example**
::

	dnRouter# clear access-lists counters
	dnRouter# clear access-lists counters ge100-1/1/1
	dnRouter# clear access-lists counters ge100-1/1/1 ipv4
	dnRouter# clear access-lists counters ge100-1/1/1 ipv4 MyAclName

.. **Help line:** clear access-lists counters

**Command History**

+-------------+-----------------------------------------------------+
|             |                                                     |
| Release     | Modification                                        |
+=============+=====================================================+
|             |                                                     |
| 5.1.0       | Command introduced                                  |
+-------------+-----------------------------------------------------+
|             |                                                     |
| 6.0         | Replaced acl with access-list                       |
+-------------+-----------------------------------------------------+
|             |                                                     |
| 7.0         | Replaced access-list with access-lists in syntax    |
+-------------+-----------------------------------------------------+