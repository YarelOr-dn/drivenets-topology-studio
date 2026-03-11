system event-manager periodic-policy user
-----------------------------------------

**Minimum user role:** admin

You can configure a user-name and role to execute the policy commands. The user-name must be from a local admin user group (AAA users are not supported). If the user-name role is changed to any other than admin, the policy will become "inactive" on the next execution.

**Command syntax: user [user-name]**

**Command mode:** config

**Hierarchies**

- system event-manager periodic-policy


**Note**

- Notice the change in prompt

.. - "user-name" is a mandatory parameter and commit will fail if no user-name was configured for policy.

    - user-name must be from local admin user-group, AAA users are not supported, in case user-name role will be changed to other than admin, the policy will become "inactive" on the next execution.

    - user from admin group user can configure "user-name" from any local group except techsupport group, the script will be executed according to user-name role.

    - there is no "no command", user-name can't be removed.

**Parameter table**

+-----------+-----------------------+--------+---------+
| Parameter | Description           | Range  | Default |
+===========+=======================+========+=========+
| user-name | The name of the user. | String | \-      |
+-----------+-----------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-periodic-manager)# periodic-policy test
    dnRouter(cfg-periodic-policy-test)# user dnroot


.. **Help line:** configure user-name and role that will execute the policy commands.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


