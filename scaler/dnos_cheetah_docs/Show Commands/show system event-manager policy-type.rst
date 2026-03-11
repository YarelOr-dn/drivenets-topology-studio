show system event-manager policy-type
-------------------------------------

**Minimum user role:** viewer

To display the operational state and information about a specific policy type or a specific policy under a specific policy type.



**Command syntax: show system event-manager policy-type [policy-type]** policy-name [policy-name]

**Command mode:** operational



.. 
   **Internal Note**

    - general command shows counters and states for all policies per policy-type.

    - show per "policy-name" command will show a specific counters and states of the policy-name.

    - commands presents both configuration and operation data of user policies.

    - policy is inactive oper-state if admin-state is disabled or it finished its execution, otherwise its state it active.

**Parameter table**

+----------------+------------------------------+-----------------+
| Parameter Name | Description                  | Values          |
+================+==============================+=================+
| policy-type    | The type of policy           | event-policy    |
|                |                              | periodic-policy |
|                |                              | generic-policy  |
+----------------+------------------------------+-----------------+
| policy-name    | The name of the given policy | \-              |
+----------------+------------------------------+-----------------+

The following information is displayed:

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| Parameter Name      | Description                                                                                                                                     | Values                                                   |
+=====================+=================================================================================================================================================+==========================================================+
| name                | Name of the policy given by the user.                                                                                                           | string                                                   |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| iterations interval | Periodic - policy configuration recurrence.                                                                                                     | periodic: DD HH:MM:SS (Range 1M - 30D)                   |
|                     | On-Time - the frequency the policy is executed by an exact time frame.                                                                          | on-time: HH:MM:SS Mon, Tue, Wed, Fri, Sat, Sun, Everyday |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| next iteration      | The time left until the next policy execution.                                                                                                  | DD HH:MM:SS                                              |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| admin-state         | The policy admin state.                                                                                                                         | enabled, disabled                                        |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| oper-state          | The policy operational state. A policy is inactive if the admin-state is disabled or the policy has finished running.                           | active, inactive                                         |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| user name           | The configured user-name to execute commands.                                                                                                   | \-                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| script              | The configured policy-script name to that will run upon policy exec                                                                             | \-                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| match count         | Counts the current number of event-policy regex matches occurred during the configured time-interval, once policy executed this counter resets. | \-                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| script maxruntime   | The configured script maximum time to run.                                                                                                      | \-                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| max iterations      | The configured number of policy iterations.                                                                                                     | \-                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+
| executed iterations | The actual number of policy iterations                                                                                                          | \-                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------+

**Example**
::

   dnRouter# show system event-manager policy-type event-policy

    Event-policies:
    | name     | admin-state | oper-state | user name  | script        | max iterations | executed iterations | match count | script maxruntime |
    |----------+-------------+------------+------------+---------------+----------------+---------------------+-------------+-------------------|
    | show-cmd | enabled     | active     | dnoperator | show_sys.py   | 30             | 20                  | 100         | 300               |
    | get-cnt  | enabled     | inactive   | dnoperator | get_tx_cnt.py | 100            | 100                 | 150         | 200               |
    | status   | disabled    | inactive   | dnoperator | get_status.py | 100            | -                   | -           | 200               |

    dnRouter# show system event-manager policy-type periodic-policy

    Periodic-policies:
    | name     | admin-state | oper-state | user name | script        | max iterations | executed iterations | iterations interval        | next iteration   | script maxruntime |
    |----------+-------------+------------+-----------+---------------+----------------+---------------------+----------------------------+------------------+-------------------|
    | status   | disabled    | inactive   | operator  | get_status.py | 100            | -                   | on-time everyday, 11:00:00 | -                | 200               |

    dnRouter# show system event-manager policy-type generic-policy

    Generic-policies:
    | name     | admin-state | oper-state | user name  | script        |
    |----------+-------------+------------+------------+---------------|
    | get-cnt  | enabled     | inactive   | myoperator | get_tx_cnt.py |


    dnRouter# show system event-manager policy-type event-policy policy-name show-cmd

    | name     | admin-state | oper-state | user name  | script        | max iterations | executed iterations | match count | script maxruntime |
    |----------+-------------+------------+------------+---------------+----------------+---------------------+-------------+-------------------|
    | show-cmd | enabled     | active     | dnoperator | show_sys.py   | 30             | 20                  | 100         | 300               |

.. **Help line:** The name of the policy.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

