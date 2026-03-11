routing-policy flowspec-local-policies ipv4 policy
--------------------------------------------------

**Minimum user role:** operator

To configure an ipv4 policy:

**Command syntax: policy [policy-name]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4

**Note**

- Legal string length is 1-255 characters.

- Illegal characters include any whitespace and the following special characters (separated by commas): #,!,',”,\

**Parameter table**

+-------------+-------------+------------------+---------+
| Parameter   | Description | Range            | Default |
+=============+=============+==================+=========+
| policy-name | policy name | | string         | \-      |
|             |             | | length 1-255   |         |
+-------------+-------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# policy policy-1
    dnRouter(cfg-flp-ipv4-pl)#


**Removing Configuration**

To remove the specified policy:
::

    dnRouter(cfg-rpl-flp-ipv4)# no policy policy-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
