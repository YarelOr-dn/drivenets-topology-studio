protocols segment-routing mpls auto-policy maximum-auto-policies
----------------------------------------------------------------

**Minimum user role:** operator

Maximum auto policies sets the values for the generation of system events when crossed.

To configure the SR-TE auto policies limit:

**Command syntax: maximum-auto-policies [maximum]** threshold [percent]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy

**Parameter table**

+-----------+----------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                    | Range        | Default |
+===========+================================================================+==============+=========+
| maximum   | The maximum limit of auto-policies in the system               | 1-4294967295 | 500     |
+-----------+----------------------------------------------------------------+--------------+---------+
| percent   | Percentage of the maximum limit of auto-policies in the system | 1-100        | 75      |
+-----------+----------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# maximum-auto-policies 1000

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# maximum-auto-policies 1200 threshold 80


**Removing Configuration**

To revert maximum limit and threshold to their default values:
::

    dnRouter(cfg-sr-mpls-auto-policy)# no maximum-auto-policies

To revert threshold to its default value:
::

    dnRouter(cfg-sr-mpls-auto-policy)# no maximum-auto-policies 1200 threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
