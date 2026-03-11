routing-policy flowspec-local-policies ipv6 match-class
-------------------------------------------------------

**Minimum user role:** operator

To configure an ipv6 match class:

**Command syntax: match-class [mc-name]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6

**Note**

- Legal string length must be 1-255 characters.

- Illegal characters include any whitespaces and the following special characters (separated by commas): #,!,',”,\

**Parameter table**

+-----------+------------------+------------------+---------+
| Parameter | Description      | Range            | Default |
+===========+==================+==================+=========+
| mc-name   | match class name | | string         | \-      |
|           |                  | | length 1-255   |         |
+-----------+------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the specified match class:
::

    dnRouter(cfg-rpl-flp-ipv6)# no match-class mc-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
