interfaces ndp router-advertisement
-----------------------------------

**Minimum user role:** operator

To enter ndp router-advertisement configuration level:

**Command syntax: ndp router-advertisement**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:
  - IRB

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# irb1
    dnRouter(cfg-if-irb1)# ndp router-advertisement
    dnRouter(cfg-if-irb1-ndp-ra)#


**Removing Configuration**

To clear all NDP router-advertisement settings:
::

    - dnRouter(cfg-if-irb1)# no ndp router-advertisement

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
