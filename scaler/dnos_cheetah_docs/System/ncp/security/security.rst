system ncp security
-------------------

**Minimum user role:** operator

Enter security related configuration settings.

To configure security parameters:

**Command syntax: security**

**Command mode:** config

**Hierarchies**

- system ncp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# security
    dnRouter(cfg-system-ncp-7-security)#


**Removing Configuration**

To revert security to its default value:
::

    dnRouter(cfg-system-ncp-7)# no security

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
