nacm dynamic-nacm admin-state
-----------------------------

**Minimum user role:** admin

To enable or disable dynamic NETCONF access control enforcement: If 'true', then enforcement is enabled.  If 'false', then enforcement is disabled.

**Command syntax: dynamic-nacm admin-state [enable-dynamic-nacm]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter           | Description                                                                      | Range        | Default |
+=====================+==================================================================================+==============+=========+
| enable-dynamic-nacm | Enables or disables dynamic NETCONF access control enforcement.  If 'true', then | | enabled    | False   |
|                     | enforcement is enabled.  If 'false', then enforcement is disabled.               | | disabled   |         |
+---------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# dynamic-nacm admin-state enabled


**Removing Configuration**

To revert dynamic enforcement to the default value:
::

    dnRouter(cfg-nacm)# no dynamic-nacm admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
