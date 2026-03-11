routing-policy flowspec-local-policies
--------------------------------------

**Minimum user role:** operator

To configure a policy based routing rule:

**Command syntax: flowspec-local-policies**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- Legal string length is 1-255 characters.

- Illegal characters include any whitespace and the following special characters (separated by commas): #,!,',”,\

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)#


**Removing Configuration**

To remove the specified flowspec-local-policies rule:
::

    dnRouter(cfg-rpl)# no flowspec-local-policies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
