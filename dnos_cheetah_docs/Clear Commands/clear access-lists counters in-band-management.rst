clear access-lists counters in-band-management
----------------------------------------------

**Minimum user role:** operator

To clear the control plane in-band management access-list counters:

**Command syntax: clear access-lists counters in-band-management** [access-list-type] [access-list-name]

**Command mode:** operation

.. **Hierarchies**



.. **Note**
 - Clear access-lists counters in-band-management - clears all Control Plane ACL rules counters for both ACL types
 - Clear access-lists counters in-band-management [access-list-type] - clears Control Plane ACL rules for the specified ACL type
 - Clear access-lists counters in-band-management [access-list-name] - clears Control Plane ACL rules for the specified ACL name.

**Parameter table**

+---------------------+-------------------------------------------------------------+----------------------------------------+---------+
|                     |                                                             |                                        | Default |
| Parameter           | Description                                                 | Range                                  |         |
+=====================+=============================================================+========================================+=========+
|                     |                                                             |                                        |         |
| access-list-type    | Clears the counters for the specified access-list type      | IPv4                                   |         |
|                     |                                                             |                                        | \ -     |
|                     |                                                             | IPv6                                   |         |
+---------------------+-------------------------------------------------------------+----------------------------------------+---------+
|                     |                                                             |                                        |         |
| access-list-name    | Clears the counters for the specified access-list           | The name of an existing access-list    |\ -      |
+---------------------+-------------------------------------------------------------+----------------------------------------+---------+

**Example**
::

	dnRouter# clear access-lists counters in-band-management
	dnRouter# clear access-lists counters in-band-management ipv4
	dnRouter# clear access-lists counters in-band-management CP_ACL_IPv6
	dnRouter# clear access-lists counters in-band-management ipv4 CP_ACL_IPv4

.. **Help line:** Clears control plane in-band-management access list counters

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+
