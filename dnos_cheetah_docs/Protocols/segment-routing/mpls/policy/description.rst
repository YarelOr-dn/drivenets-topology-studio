protocols segment-routing mpls policy description
-------------------------------------------------

**Minimum user role:** operator

It is good practice to provide a meaningful description of the policy.

To configure a description of the policy:


**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-------------+--------------------+------------------+---------+
| Parameter   | Description        | Range            | Default |
+=============+====================+==================+=========+
| description | policy description | | string         | \-      |
|             |                    | | length 1-255   |         |
+-------------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy POL_1
    dnRouter(cfg-sr-mpls-policy)# description "this is my segment-routing policy"


**Removing Configuration**

To remove the configured description:
::

    dnRouter(cfg-sr-mpls-policy)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
