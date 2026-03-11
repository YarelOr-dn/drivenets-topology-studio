routing-policy flowspec-local-policies ipv4 policy description
--------------------------------------------------------------

**Minimum user role:** operator

To add an optional description for the policy.

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 policy

**Parameter table**

+-------------+-------------------------+------------------+---------+
| Parameter   | Description             | Range            | Default |
+=============+=========================+==================+=========+
| description | ipv4 policy description | | string         | \-      |
|             |                         | | length 1-255   |         |
+-------------+-------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# policy policy-1
    dnRouter(cfg-flp-ipv4-pl)# description "The policy"
    dnRouter(cfg-flp-ipv4-pl)#


**Removing Configuration**

To revert the description to default:
::

    dnRouter(cfg-flp-ipv4-pl)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
