protocols segment-routing mpls auto-policy template color
---------------------------------------------------------

**Minimum user role:** operator

To create SR-TE auto policy templates for Segment-Routing policies that will be created automatically upon requests matching the color:

**Command syntax: template color [color]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy

**Note**
- Two policies from the same head to the same tail with the same color cannot exist, regardless of their origin.

- Deletion of the auto-policy templates will delete the associated policies created by these templates.

**Parameter table**

+-----------+----------------------+--------------+---------+
| Parameter | Description          | Range        | Default |
+===========+======================+==============+=========+
| color     | SR auto-policy color | 0-4294967295 | \-      |
+-----------+----------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)#


**Removing Configuration**

To remove a specific auto policy template:
::

    dnRouter(cfg-sr-mpls-auto-policy)# no template color 3

To remove all configured auto policy templates:
::

    dnRouter(cfg-sr-mpls-auto-policy)# no template

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
