clear ipsec counters
----------------------

**Minimum user role:** operator

To clear counters per specific IPSec tunnel.

**Command syntax: clear ipsec counters** [tunnel-id]

**Command mode:** operation

.. **Hierarchies**

**Parameter table:**

+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+
|               |                                                                                                                 |                                                                   |             |
| Parameter     | Description                                                                                                     | Range                                                             | Default     |
+===============+=================================================================================================================+===================================================================+=============+
|               |                                                                                                                 | Any configured IPSec tunnel                                       |             |
| tunnel-id     | Enter name of the specific IPSec tunnel                                                                         |                                                                   | \-          |
+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+

**Example**
::

	dnRouter# clear ipsec counters TUNNEL_1
	Counters where cleared for IPSec tunnel TUNNEL_1


.. **Help line:** Clear counters per specific IPSec tunnel

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.3        | Command introduced    |
+-------------+-----------------------+
