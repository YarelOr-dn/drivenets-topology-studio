protocols bgp bestpath rpki prefix-validate
-------------------------------------------

**Minimum user role:** operator

You can use this command to enable the RPKI origin-AS validation, and the validation states of BGP routes and their preference are taken into consideration for the BGP bestpath calculation.

To configure the rpki prefix-validation:

**Command syntax: bestpath rpki prefix-validate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- By default rpki prefix-validate is enabled.

- The no command returns prefix-validate to its default value.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------------------+---------+
| Parameter   | Description                                                                      | Range             | Default |
+=============+==================================================================================+===================+=========+
| admin-state | Enables RPKI origin-AS validation and the validity states of BGP paths to affect | | enabled         | enabled |
|             | the path's preference in the BGP bestpath process.                               | | disabled        |         |
|             |                                                                                  | | allow-invalid   |         |
+-------------+----------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter(cfg-protocols-bgp)# bestpath rpki prefix-validate disabled
    dnRouter(cfg-protocols-bgp)# bestpath rpki prefix-validate allow-invalid


**Removing Configuration**

To revert the prefix-validate to its default value: 
::

    dnRouter(cfg-protocols-bgp)# no bestpath rpki prefix-validate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
