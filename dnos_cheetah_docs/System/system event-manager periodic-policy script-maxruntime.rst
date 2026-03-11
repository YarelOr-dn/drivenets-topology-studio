system event-manager periodic-policy script-maxruntime
------------------------------------------------------

**Minimum user role:** admin

To configure the policy execution max-runtime:.

**Command syntax: script-maxruntime [runtime]**

**Command mode:** config

**Hierarchies**

- system event-manager periodic-policy


**Note**

- Any updates to the script-maxruntume configuration during a policy execution are implemeted at the next policy execution.

- Once the script-maxruntime value is reached, the policy is terminated even if it in the middle of an execution.

- During a policy execution no another execution is initiated with the same policy rule (policy-name)

.. -  script-maxruntime must be less than the policy-interval, otherwise the configuration will be rejected.

**Parameter table**

+-------------------------+-----------------------------------------------------+-----------------------------+---------------+
| Parameter               | Description                                         | Range                       | Default       |
+=========================+=====================================================+=============================+===============+
| script-maxruntime       | The maximum time before the policy is stopped.      | 5 - 600 (seconds)           | 30            |
+-------------------------+-----------------------------------------------------+-----------------------------+---------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# periodic-policy test
    dnRouter(cfg-periodic-policy-test)# script-maxruntime 300
    dnRouter(cfg-periodic-policy-test)#

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-periodic-policy-test)# no script-maxruntime

.. **Help line:** configure the runtime duration of the policy in seconds.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


