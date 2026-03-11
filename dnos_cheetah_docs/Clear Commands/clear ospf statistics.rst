clear ospf statistics
---------------------

**Minimum user role:** operator

Use the following command to clear the OSPF statistics. If an interface is specified the counters for the specific interface will be cleared:

**Command syntax: clear ospf** instance [ospf-instance-name] **statistics** interface [ interface-name ]

**Command mode:** operation

.. **Hierarchies**

**Note**

- clearing an interface counters must not impact the global counters and vice versa.

- use "instance [ospf-instance-name]" to clear information from a specific OSPF instance, when not specified, clear information from all OSPF instances

**Parameter table:**

+--------------------+----------------------------------------------------------------+---------------------------------------------------+-------------+
|                    |                                                                |                                                   |             |
| Parameter          | Description                                                    | Range                                             | Default     |
+====================+================================================================+===================================================+=============+
|                    |                                                                |                                                   |             |
| interface-name     | clears the ospf statistics for the specified interface         | ge<interface speed>-<A>/<B>/<C>                   | \-          |
|                    |                                                                |                                                   |             |
|                    |                                                                | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|             |
|                    |                                                                |                                                   |             |
|                    |                                                                | bundle-<bundle id>                                |             |
|                    |                                                                |                                                   |             |
|                    |                                                                | bundle-<bundle id>.<sub-interface id>             |             |
|                    |                                                                |                                                   |             |
|                    |                                                                | lo<lo-interface id>                               |             |
+--------------------+----------------------------------------------------------------+---------------------------------------------------+-------------+
| ospf-instance-name | clears the ospf information for the specified instance         | configured instances names                        | all         |
+--------------------+----------------------------------------------------------------+---------------------------------------------------+-------------+

**Example**
::

	dnRouter# clear ospf statistics
	dnRouter# clear ospf instance instance1 statistics

.. **Help line:** Clear OSPF statistics

**Command History**

+-------------+------------------------+
|             |                        |
| Release     | Modification           |
+=============+========================+
|             |                        |
| 11.6        | Command introduced     |
+-------------+------------------------+
| 18.2        | Add instance parameter |
+-------------+------------------------+
