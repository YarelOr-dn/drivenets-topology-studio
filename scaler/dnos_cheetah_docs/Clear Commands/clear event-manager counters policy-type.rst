clear event-manager counters policy-type
----------------------------------------

**Minimum user role:** operator

Use this command to clear all policy counters, or the counters for a specific policy type.

**Command syntax: clear event-manager counters policy-type [policy-type]** policy-name [policy-name]

**Command mode:** operation

.. **Hierarchies**

**Note**

- When the policy-name is specified the command clears all policy counters per policy-type per policy name.

- clear event-manager counters policy-type - clears all policy counters per policy type, for the following policy types:

  - event-policy - policy that will be executed upon matching trigger of registered system event.
 
  - periodic-policy - a recurrent policy according to the scheduled configuration, with limited execution time.
 
  - generic-policy - policy that will be executed only once and unlimited in execution time.

**Parameter table**

+----------------+-----------------------+-------------------+---------+
|                |                       |                   | Default |
| Parameter      | Description           | Range             |         |
+================+=======================+===================+=========+
|                |                       |                   | \ -     |
| policy-type    | The type of policy    | event-policy      |         |
|                |                       |                   |         |
|                |                       | periodic-policy   |         |
|                |                       |                   |         |
|                |                       | generic-policy    |         |
+----------------+-----------------------+-------------------+---------+


**Example**
::

    dnRouter# clear event-manager counters policy-type periodic-policy
    dnRouter# clear event-manager counters policy-type generic-policy policy-name test



.. **Help line:** insert the policy-name who's counters shall be cleared.

**Command History**

+-------------+------------------------------------+
|             |                                    |
| Release     | Modification                       |
+=============+====================================+
|             |                                    |
| 11.2        | Command introduced                 |
+-------------+------------------------------------+