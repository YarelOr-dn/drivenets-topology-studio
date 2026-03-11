system event-manager event-policy script-name
---------------------------------------------

**Minimum user role:** admin

Use this command to configure the name of the script-name to be executed. If the script is deleted, the policy operational state becomes "inactive". Once an event policy has completed, it cannot be triggered again for 30 seconds.

**Command syntax: script-name [script-name]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt

.. - event-policy scripts shall be located under /event-manager/event-policy/scripts dir.

    - Once policy terminated a 30 seconds suspension will be issued before next policy execution.

    - there is no "no command", policy-script can't be removed.

    - "script-name" is a mandatory parameter and commit will fail if no script-name was configured for policy.

    - In case of script-name file deletion, policy operational-state will become inactive.

    Validation:

    - script-name can be used by several policy-names as long as the system-events are different.

**Parameter table**

+-------------+---------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                                                             | Range  | Default |
+=============+=========================================================================================================+========+=========+
| script-name | The name of the script-file which must be located in the /event-manager/event-policy/scripts directory. | string | \-      |
|             | This is a mandatory parameter. The commit will fail if no script name has been configured.              |        |         |
+-------------+---------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)#
    dnRouter(cfg-event-policy-test)# script-name event_policy_example.py
    dnRouter(cfg-event-policy-test)#


.. **Help line:** configure the script-name name that will be executed.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


