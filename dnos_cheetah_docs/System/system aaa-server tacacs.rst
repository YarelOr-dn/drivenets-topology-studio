system aaa-server tacacs
------------------------

**Minimum user role:** operator

To define a remote TACACS+ server:

**Command syntax: tacacs**

**Command mode:** config

**Hierarchies**

- system aaa-server

**Note**
.. - "no tacacs" removes TACACS AAA configuration


**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)#


**Removing Configuration**

To delete the tacacs configuration:
::

    dnRouter(cfg-system-aaa)# no tacacs

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 11.0    | Command introduced                           |
+---------+----------------------------------------------+
| 13.1    | Added support for OOB management (VRF mgmt0) |
+---------+----------------------------------------------+
| 15.1    | Added support for IPv6 address format        |
+---------+----------------------------------------------+
