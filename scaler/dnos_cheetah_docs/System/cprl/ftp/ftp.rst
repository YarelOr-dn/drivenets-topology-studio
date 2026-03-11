system cprl ftp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the FTP protocol:

**Command syntax: ftp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ftp
    dnRouter(cfg-system-cprl-ftp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the FTP protocol:
::

    dnRouter(cfg-system-cprl)# no ftp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
