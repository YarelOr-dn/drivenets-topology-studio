clear ospfv3 statistics
-----------------------

**Minimum user role:** operator

Use the following command to clear the OSPFv3 statistics. If an interface is specified the counters for the specific interface will be cleared:

**Command syntax: clear ospfv3 statistics** interface [ interface-name ]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clearing an interface counters must not impact the global counters and vice versa.

**Parameter table:**

+-------------------+-------------------------------------------------------------+---------------------------------------------------+-------------+
|                   |                                                             |                                                   |             |
| Parameter         | Description                                                 | Range                                             | Default     |
+===================+=============================================================+===================================================+=============+
|                   |                                                             |                                                   |             |
| interface-name    | clears the ospfv3 statistics for the specified interface    | ge<interface speed>-<A>/<B>/<C>                   | all         |
|                   |                                                             |                                                   |             |
|                   |                                                             | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|             |
|                   |                                                             |                                                   |             |
|                   |                                                             | bundle-<bundle id>                                |             |
|                   |                                                             |                                                   |             |
|                   |                                                             | bundle-<bundle id>.<sub-interface id>             |             |
|                   |                                                             |                                                   |             |
|                   |                                                             | lo<lo-interface id>                               |             |
+-------------------+-------------------------------------------------------------+---------------------------------------------------+-------------+

**Example**
::

	dnRouter# clear ospfv3 statistics
	dnRouter# clear ospfv3 statistics interafce bundle-12.1234


.. **Help line:** Clear OSPFv3 statistics

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.6        | Command introduced    |
+-------------+-----------------------+