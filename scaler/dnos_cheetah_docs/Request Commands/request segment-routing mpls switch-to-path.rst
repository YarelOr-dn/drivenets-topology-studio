request segment-routing mpls switch-to-path
-------------------------------------------

**Minimum user role:** operator

Invoke path validation for path with requested priority of requested SR-TE policy.
In case path is found to be valid, install path as active, regardless of active path prioty and if it has lock

In case path found as invalid (due to no routing solution or bfd depended and bfd timeout) request is revoke and forgotten


To invoke SR-TE policy candidate path switch:


**Command syntax: request segment-routing mpls switch-to-path policy [policy-name] path-priority [priority]**

**Command mode:** operator

**Note:**

- This action does not affect the configuration and it is not persistent.
- Next policy reoptimization may result in replacing the requested path with new active path
- In case the requested path is already installed backup path, switching it to become active will also trigger new path selection for the backup path
- Once requested path is installed as active, lock logic will apply for it, if such was configured to path




**Parameter table:**

+---------------+---------------------------------------------------------+
| Parameter     | Description                                             |
+===============+=========================================================+
| policy-name   | Select SR-TE policy to switch active path               |
+---------------+---------------------------------------------------------+
| path-priority | the path priority value for which switching is desired  |
+---------------+---------------------------------------------------------+


**Example:**
::

	dnRouter# request segment-routing mpls switch-to-path policy MY_SR_TE_POLICY path-priority 3

.. **Help line:** Switch policy active path to requested SR-TE candidate path


**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 18.3      | Command introduced    |
+-----------+-----------------------+
