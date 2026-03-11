system ncp security signature-validation admin-state
----------------------------------------------------

**Minimum user role:** admin

Enable signature validation functionality or disable and remove its configuration.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ncp security signature-validation

**Parameter table**

+-------------+---------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                         | Range        | Default  |
+=============+=====================================================================+==============+==========+
| admin-state | Indicates whether signature validation is administratively enabled. | | enabled    | disabled |
|             |                                                                     | | disabled   |          |
+-------------+---------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# security
    dnRouter(cfg-system-ncp-7-security)# signature-validation
    dnRouter(cfg-system-ncp-7-security-signature-validation)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-system-ncp-7-security-signature-validation)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
