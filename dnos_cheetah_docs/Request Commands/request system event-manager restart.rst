request system event-manager restart
------------------------------------

**Minimum user role:** admin

Use this command to reset statistics counters for all policy types and stop running policies. Any policies with an admin-state "enabled" are restarted and their operational state changes to active. Any policies that have a "disabled" admin-state will remain in the operational-state "inactive".

To restart a specific policy type, use the policy-type command:

**Command syntax: request system event-manager restart** policy-type [policy-type]

**Command mode:** operational

**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|                |                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                               |
| Parameter      | Description                                                                                                                                                                                                                                                                                                                                                                          | Range                                                                                                         |
+================+======================================================================================================================================================================================================================================================================================================================================================================================+===============================================================================================================+
|                |                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                               |
| Policy-type    | Specify to   restart all policies of the same type.                                                                                                                                                                                                                                                                                                                                  | Policy types:                                                                                                 |
|                |                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                               |
|                | If you don’t   specify a policy-type, all policies will be restarted. Statistics counters will   be zeroed, existing policies executions will stop. Any policy with   admin-state "enabled" will be re-lunched and its operational state   will be changed to “active”. The policies of current type that are in   admin-state disable will stay in operational-state "inactive".    | event-policy - policy that will be executed upon   matching trigger of registered system event.               |
|                |                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                               |
|                |                                                                                                                                                                                                                                                                                                                                                                                      | periodic-policy - a recurrent policy according to   the scheduled configuration, with limited execution time. |
|                |                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                               |
|                |                                                                                                                                                                                                                                                                                                                                                                                      | generic-policy - policy that will be executed   only once and unlimited in execution time.                    |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+

**Example**

To restart all policy types:
::

    dnRouter#
    dnRouter# request system event-manager restart
    dnRouter#

To restart a specific policy type, such as the periodic-policy
::

    dnRouter# request system event-manager restart policy-type periodic-policy
    dnRouter#

.. **Help line:** Restart all policies according to policy type, and delete policies operational-data

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+