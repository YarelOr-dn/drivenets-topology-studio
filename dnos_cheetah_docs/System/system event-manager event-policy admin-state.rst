system event-manager event-policy admin-state
---------------------------------------------

**Minimum user role:** admin

Use this command to configure the policy admin-state. An enabled admin-state activates the policy and the operational-state becomes "active". Disabled stops any policy execution, clears the policy counters and the operational-state becomes "inactive". If a policy is enabled, but the policy’s username or script-name weren't configured, the policy operational-state remains "inactive" and the policy won't be executed.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt.

- This change takes effect immediately.

.. - Changing admin-state to enabled will activate the policy and policy operational-state will be active.

    - Changing admin-state to disabled, will terminate policy execution, clear policy counters and set policy operational-state to inactive

    - no command resets policy admin-state to default, will take effect immediately.

    - In case policy is enabled, but policy username or/and policy script-name weren't configured, the policy oper-state will be "inactive" and the policy won't be executed. same behavior is regarding deletion of username or script-name during policy execution will set the policy to "inactive" oper-state on next execution.

**Parameter table**

+-------------+------------------------------+--------------------+----------+
| Parameter   | Description                  | Range              | Default  |
+=============+==============================+====================+==========+
| admin-state | Sets the policy admin-state. | Enabled / Disabled | Disabled |
+-------------+------------------------------+--------------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# admin-state enabled
    dnRouter(cfg-event-policy-test)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no admin-state

.. **Help line:** configure the policy admin-state parameter.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


