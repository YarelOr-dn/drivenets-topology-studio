system ncp security measured-boot
---------------------------------

**Minimum user role:** operator

Enter measured boot related configuration settings.

To configure measured boot parameters:

**Command syntax: measured-boot**

**Command mode:** config

**Hierarchies**

- system ncp security

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# security
    dnRouter(cfg-system-ncp-7-security)# measured-boot
    dnRouter(cfg-system-ncp-7-security-measured-boot)#


**Removing Configuration**

To revert the measured-boot to its default value:
::

    dnRouter(cfg-system-ncp-7-security)# no measured-boot

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
