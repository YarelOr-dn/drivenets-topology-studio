nacm admin-state
----------------

**Minimum user role:** admin

A global 'admin-state' enabled/disabled switch is provided to enable or disable all access control enforcement. When this global switch is set to 'enabled', all requests are checked against the access control rules and only permitted if configured to allow the specific access request. When this global switch is set to 'disabled', all access requests are permitted and authorization will be performed according to role.

**Command syntax: admin-state [enable-nacm]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| enable-nacm | Enables or disables all NETCONF access control enforcement.  If 'true', then     | | enabled    | False   |
|             | enforcement is enabled.  If 'false', then enforcement is disabled.               | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# admin-state enabled


**Removing Configuration**

To revert the admin-state to the default value:
::

    dnRouter(cfg-nacm)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
