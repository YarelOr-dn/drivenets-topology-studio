show mpls label-allocation shared-pool
--------------------------------------

**Minimum user role:** viewer

This command displays MPLS label allocation status from the dynamic mpls pool shared between multiple routing protocols
To display the MPLS label allocations of the shared pool:

**Command syntax: show mpls label-allocation shared-pool**

**Command mode:** operational



**Note**


**Parameter table**


**Example**
::

	dnRouter# show mpls label-allocation shared-pool

    | Label range             | Total labels   | Protocols                   |
    |-------------------------|----------------|-----------------------------|
    | 256-7999                | 7744           | ldp, rsvp, dynamic-sr, bgp  |
    | 24000-1032381           | 1008382        | ldp, rsvp, dynamic-sr, bgp  |

    Total labels: 1016126
    Total allocated labels: 110

    | Protocol                     | Total allocated labels |
    |------------------------------|------------------------|
    | ldp                          | 0                      |
    | rsvp                         | 5                      |
    | dynamic-isis-sr              | 15                     |
    | dynamic-ospf-sr              | 0                      |
    | bgp                          | 90                     |

.. **Help line:** displays mpls label block allocation

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 18.3    | Command introduced                              |
+---------+-------------------------------------------------+
