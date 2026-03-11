system event-manager event-policy script-maxruntime
---------------------------------------------------

**Minimum user role:** admin

Use this command to configure the maximum time can run. Once the maximum time is reached the policy is terminated. During policy execution the same policy cannot be run.

**Command syntax: script-maxruntime [runtime]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt

.. - a change in the script-maxruntume configuration during policy execution will take effect on the next policy execution.

    - once script-maxruntime reached, the policy will be terminated even if it still in the middle of the execution.

    - during policy execution no another execution will be initiated of the same policy rule (policy-name)

    - no command resets script-maxruntime to default, will take effect on next policy execution.

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                                                            | Range            | Default |
+===========+========================================================================================================================+==================+=========+
| runtime   | The maximum time a policy can run before it is terminated.                                                             | 5..600 (seconds) | 30      |
|           | Any change in the script-maxruntume configuration whilst a policy is running take effect on the next policy execution. |                  |         |
+-----------+------------------------------------------------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# script-maxruntime 300
    dnRouter(cfg-event-policy-test)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no script-maxruntime

.. **Help line:** configure the runtime duration of the policy in seconds.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


