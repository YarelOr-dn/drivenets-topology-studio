routing-policy flowspec-local-policies ipv4 policy match-class
--------------------------------------------------------------

**Minimum user role:** operator

To assign an ipv4 match class to the policy:

**Command syntax: match-class [mc-name]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 policy

**Note**

- Legal string length is 1-255 characters.

- Illegal characters include any whitespace and the following special characters (separated by commas): #,!,',”,\

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
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# policy policy-1
    dnRouter(cfg-flp-ipv4-pl)# match-class mc-1
    dnRouter(cfg-ipv4-pl-mc)#


**Removing Configuration**

To remove the specified match class:
::

    dnRouter(cfg-flp-ipv4-pl)# no match-class mc-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
