system ncp security measured-boot admin-state
---------------------------------------------

**Minimum user role:** admin

Enable measured boot functionality or disable and remove its configuration.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ncp security measured-boot

**Parameter table**

+-------------+--------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                  | Range        | Default  |
+=============+==============================================================+==============+==========+
| admin-state | Indicates whether measured boot is administratively enabled. | | enabled    | disabled |
|             |                                                              | | disabled   |          |
+-------------+--------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# security
    dnRouter(cfg-system-ncp-7-security)# measured-boot
    dnRouter(cfg-system-ncp-7-security-measured-boot)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-system-ncp-7-security-measured-boot)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
