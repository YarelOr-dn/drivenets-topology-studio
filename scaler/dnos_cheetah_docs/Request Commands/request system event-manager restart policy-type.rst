request system event-manager restart policy-type
------------------------------------------------

**Minimum user role:** admin

Use this command to reset statistics counters for the specified policy type and stop its running policies. Any policies within the specified type with an admin-state "enabled" are started again and their operational state changes to active. The policies that have an admin-state "disabled" will remain in the operational-state "inactive". You can also reset a specific policy under a specific policy type.

**Command syntax: request system event-manager restart policy-type [policy-type]** policy-name [policy-name]

**Command mode:** operational

**Parameter table**

+----------------+-----------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|                |                                                     |                                                                                                               |
| Parameter      | Description                                         | Range                                                                                                         |
+================+=====================================================+===============================================================================================================+
|                |                                                     |                                                                                                               |
| Policy-type    | Specify to   restart all policies of the same type. | Policy types:                                                                                                 |
|                |                                                     |                                                                                                               |
|                |                                                     | event-policy - policy that will be executed upon   matching trigger of registered system event.               |
|                |                                                     |                                                                                                               |
|                |                                                     | periodic-policy - a recurrent policy according to   the scheduled configuration, with limited execution time. |
|                |                                                     |                                                                                                               |
|                |                                                     | generic-policy - policy that will be executed   only once and unlimited in execution time.                    |
+----------------+-----------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|                |                                                     |                                                                                                               |
| Policy-name    | Specify to   restart a specific policy.             | String                                                                                                        |
+----------------+-----------------------------------------------------+---------------------------------------------------------------------------------------------------------------+

**Example**

To restart all policies of a specific type:
::

    dnRouter#
    dnRouter# request system event-manager restart policy-type periodic-policy
    dnRouter#

To restart a specific policy, such as the generic-policy named get-cnt:
::

    dnRouter# request system event-manager restart policy-type generic-policy policy-name test
    dnRouter#

.. **Help line:** this action will restart all policies according to policy type, and delete policies operational-data.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+