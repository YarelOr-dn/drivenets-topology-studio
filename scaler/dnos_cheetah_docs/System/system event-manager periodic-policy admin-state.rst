system event-manager periodic-policy admin-state
------------------------------------------------

**Minimum user role:** admin

To configure the policy admin-state.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system event-manager periodic-policy


**Note**

- Changing the admin-state to disabled terminates policy execution, clears policy counters, and sets policy operational-state to inactive.

- If a policy is enabled, but the policy username or/and policy script-name weren't configured, the policy oper-state will be "inactive" and the policy won't be executed. This behaviour is similar when a username or script-name is deleted. The policy execution is set to "inactive".

**Parameter table**

+-------------------------+-----------------------------------------------------+-----------------------------+---------------+
| Parameter               | Description                                         | Range                       | Default       |
+=========================+=====================================================+=============================+===============+
| admin-state             | Enable or disable the policy.                       | enabled / disabled          | disabled      |
+-------------------------+-----------------------------------------------------+-----------------------------+---------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# periodic-policy test
    dnRouter(cfg-periodic-policy-test)# admin-state enabled
    dnRouter(cfg-periodic-policy-test)#

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-periodic-policy-test)# no admin-state

.. **Help line:** configure the policy admin-state parameter.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


