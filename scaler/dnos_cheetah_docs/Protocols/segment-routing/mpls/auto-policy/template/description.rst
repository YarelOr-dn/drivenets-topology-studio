protocols segment-routing mpls auto-policy template color description
---------------------------------------------------------------------

**Minimum user role:** operator

It is good practice to provide a meaningful description of the template and policies.

To configure a description for the SR-TE auto policy template that shall also be used for policies created with the template:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# description "this is my auto-policy"


**Removing Configuration**

To remove the configured description:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
