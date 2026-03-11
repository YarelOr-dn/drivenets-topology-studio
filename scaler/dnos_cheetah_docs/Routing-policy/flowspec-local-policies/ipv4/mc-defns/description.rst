routing-policy flowspec-local-policies ipv4 match-class description
-------------------------------------------------------------------

**Minimum user role:** operator

To add an optional description for the match class:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

**Parameter table**

+-------------+------------------------------+------------------+---------+
| Parameter   | Description                  | Range            | Default |
+=============+==============================+==================+=========+
| description | ipv4 match class description | | string         | \-      |
|             |                              | | length 1-255   |         |
+-------------+------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# description "The match class"
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-flp-ipv4-mc)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
