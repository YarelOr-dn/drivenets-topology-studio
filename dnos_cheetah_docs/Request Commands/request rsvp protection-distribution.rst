request rsvp protection-distribution
------------------------------------

**Minimum user role:** operator

To run immediate protected bandwidth distribution:

**Command syntax: request rsvp protection-distribution**

**Command mode:** operational

**Note**

- Bypass tunnels that are protecting the same interface and have the same destination will balance which primary LSPs they protect, in order to balance the aggregated protected-bw between bypasses.


**Example**
::

	dnRouter# request rsvp protection-distribution


.. **Help line:** Run immidiate protected-bw balancing

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.2        | Command introduced    |
+-------------+-----------------------+