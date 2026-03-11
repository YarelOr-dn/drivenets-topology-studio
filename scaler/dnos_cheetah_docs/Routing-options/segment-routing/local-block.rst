routing-options segment-routing mpls local-block
------------------------------------------------

**Minimum user role:** operator

The segment routing local block (SRLB) is a set of labels that have local significance only.
By default, the segment-routing capable protocols use the SRGB/SRLB range configured under the routing-options hierarchy level, unless a specific block is configured under the protocol level.
To configure the segment routing local block (SRLB) used by the router:

**Command syntax: local-block [lower-bound] [range]**

**Command mode:** config

**Hierarchies**

- routing-options segment-routing mpls

**Note**

- When changing the configuration, the new block will only apply on the next system restart. To view the configured labels blocks and the currently in used label blocks, use the show mpls label-allocation tables command.

- SRGB and SRLB blocks must be identical for all instances and must not overlap.

- SRGB and SRLB blocks must not overlap

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter   | Description                                                                      | Range       | Default |
+=============+==================================================================================+=============+=========+
| lower-bound | Lower bound of the local label block. The block is defined to include this       | 256-1040383 | 8000    |
|             | label. Block range is 8k                                                         |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+
| range       | Define the srlb block size. for size of 1, only the lower-bound label exist in   | 1-32000     | 8000    |
|             | block                                                                            |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# segment-routing mpls
    dnRouter(cfg-routing-option-sr)# local-block 8000 1000


**Removing Configuration**

To revert to the default values: 
::

    dnRouter(cfg-routing-option-sr)# no local-block

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 14      | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 15      | Updated lower-bound from min 16 to min 256                     |
+---------+----------------------------------------------------------------+
| 18.3    | Updated lower-bound paramter range and add range configuration |
+---------+----------------------------------------------------------------+
