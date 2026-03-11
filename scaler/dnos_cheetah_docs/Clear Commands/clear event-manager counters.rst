clear event-manager counters
----------------------------

**Minimum user role:** operator

Use this command to clear all policy counters, or the counters for a specific policy type.

**Command syntax: clear event-manager counters** policy-type [policy-type]

**Command mode:** operation

.. **Hierarchies**

**Note**

- clear event-manager counters - clears all policy counters.

- clear event-manager counters policy-type - clears all policy counters per policy type, for the following policy types:

  - event-policy - policy that will be executed upon matching trigger of registered system event.

  - periodic-policy - a recurrent policy according to the scheduled configuration, with limited execution time.

  - generic-policy - policy that will be executed only once and unlimited in execution time.

**Parameter table:**

+--------------------+-----------------------+-----------------+-------------+
|                    |                       |                 |             |
| Parameter Name     | Description           | Range           | Default     |
+====================+=======================+=================+=============+
|                    |                       | event-policy    | \-          |
| policy-type        | The type of policy    |                 |             |
|                    |                       | periodic-policy |             |
|                    |                       |                 |             |
|                    |                       | generic-policy  |             |
+--------------------+-----------------------+-----------------+-------------+


**Example**
::

    dnRouter#
    dnRouter# clear event-manager counters
    dnRouter# clear event-manager counters policy-type periodic-policy
    dnRouter# clear event-manager counters policy-type generic-policy
    dnRouter# clear event-manager counters policy-type event-policy
    dnRouter#

.. **Help line:** this action will clear all policies counters.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+