protocols segment-routing mpls path segment-list
------------------------------------------------

**Minimum user role:** operator

A segment-list defines a path according to the different segments (SIDs) specified for it. Multiple segment-lists within the same path can be used to apply weighted ECMP of traffic forwarding between the different segment-lists.

The path must be valid for a policy to be able to use it. A path is valid only if all segment-lists with in it are valid. A segment-list is invalid if:

•	The segment-list is empty.
•	The head-end is unable to perform a path resolution for the first SID into one or more outgoing interface(s) and next-hop(s).
•	The head-end is unable to perform a SID resolution for any prefix-SID other than the first into an MPLS label.
•	The SID is known with an R-flag (i.e., is propagated from a different level).
•	The SID appears more than once on the path (loop).
•	Consecutive SIDs belong to the same node.

To configure a segment-list for a path and enter its configuration hierarchy:


**Command syntax: segment-list [segment-list]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path

**Note**
Required validations:

- At least one hop is configured.


**Parameter table**

+--------------+-----------------------------------------------------+-------+---------+
| Parameter    | Description                                         | Range | Default |
+==============+=====================================================+=======+=========+
| segment-list | unique identifier of segment-list within an SR path | 1-8   | \-      |
+--------------+-----------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# segment-list 1
    dnRouter(cfg-mpls-path-sl)# hop 1 label 30000

    dnRouter(cfg-sr-mpls-path)# segment-list 2


**Removing Configuration**

To remove a specific segment-list given path:
::

    dnRouter(cfg-sr-mpls-path)# no segment-list 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
