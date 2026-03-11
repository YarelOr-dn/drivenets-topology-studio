system event-manager generic-policy script-name
-----------------------------------------------

**Minimum user role:** admin

Use this command to configure the script-name to be executed. If the script is deleted, the policy operational state becomes "inactive". Once a generic policy has completed, it cannot be triggered again for 30 seconds.

**Command syntax: script-name [script-name]**

**Command mode:** config

**Hierarchies**

- system event-manager generic-policy 


**Note**

- Notice the change in prompt.

.. - generic-policy scripts shall be located under /event-manager/generic-policy/scripts dir.

    - Each generic policy script shall be used only by one generic policy-name.

    - there is no "no command", script-name can't be removed.

    - "script-name" is a mandatory parameter and commit will fail if no script-name was configured for policy.

    - In case of script-name file deletion, policy operational-state will become inactive.

**Parameter table**

+-------------+-----------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                                                               | Range  | Default |
+=============+===========================================================================================================+========+=========+
| script-name | The name of the script-file which must be located in the /event-manager/generic-policy/scripts directory. | string | \-      |
|             | This is a mandatory parameter. The commit will fail if no script name has been configured.                |        |         |
+-------------+-----------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# policy generic-policy test
    dnRouter(cfg-generic-policy-test)# script-name generic_policy_example.py
    dnRouter(cfg-generic-policy-test)#


.. **Help line:** configure the script-name name that will be executed.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


