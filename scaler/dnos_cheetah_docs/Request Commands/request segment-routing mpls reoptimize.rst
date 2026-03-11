request segment-routing mpls reoptimize
---------------------------------------

**Minimum user role:** operator

Paths may become invalid in time due to topology changes. When a policy has multiple path options and a better priority path becomes invalid, the system will use the next preferred priority path. The policy will continue using the lower priority path even if the higher priority path is available again. To fix this, you can globally set a policy reoptimization interval that will cause the system to instruct all segment-routing policies that are not on the best path to attempt to use a better priority path (see "segment-routing mpls policy-reoptimization").

To manually invoke segment-routing policy reoptimization:

**Command syntax: request segment-routing mpls reoptimize {all | policy [name]}**

**Command mode:** operational

**Note**

- The action will not reset the periodic reoptimization timer

**Parameter table**

+-------------+---------------------------------------------------------+
| Parameter   | Description                                             |
+=============+=========================================================+
| all         | Perform the optimization action on all policies         |
+-------------+---------------------------------------------------------+
| policy-name | Perform the optimization action on the specified policy |
+-------------+---------------------------------------------------------+

**Example**
::

	dnRouter# request segment-routing mpls reoptimize all
	dnRouter# request segment-routing mpls reoptimize policy SR_POLICY_A

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+