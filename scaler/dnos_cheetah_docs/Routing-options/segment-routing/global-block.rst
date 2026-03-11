routing-options segment-routing mpls global-block
-------------------------------------------------

**Minimum user role:** operator

The segment routing global block (SRGB) is a set of labels that are reserved for segment routing and have global significance in the routing protocol domain.
The configured label block is reserved even if not used by any of the segment-routing capable protocols.
By default, the segment-routing capable protocols use the SRGB/SRLB range configured under the routing-options hierarchy level, unless a specific block is configured under the protocol level.

To configure the segment routing global block (SRGB) used by the router:

**Command syntax: global-block [lower-bound] [range]**

**Command mode:** config

**Hierarchies**

- routing-options segment-routing mpls

**Note**

- When changing the configuration, the new block will only apply on the next system restart. To view the configured labels blocks and the currently in used label blocks, use the show mpls label-allocation tables command.

- The base and range together define the block size (i.e. the number of labels in the block) and must be identical for all instances, even if segment-routing is disabled.

- SRGB and SRLB blocks must not overlap.

- SRGB and SRLB blocks must not overlap

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter   | Description                                                                      | Range       | Default |
+=============+==================================================================================+=============+=========+
| lower-bound | Lower bound of the global label block. The block is defined to include this      | 256-1036384 | 16000   |
|             | label.                                                                           |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+
| range       | Define the srgb block size. for size of 1, only the lower-bound label exist in   | 1-1000000   | 8000    |
|             | block                                                                            |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# segment-routing mpls
    dnRouter(cfg-routing-option-sr)# global-block 32000 16000


**Removing Configuration**

To revert to the default values: 
::

    dnRouter(cfg-routing-option-sr)# no global-block

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 14      | Command introduced                                         |
+---------+------------------------------------------------------------+
| 16.1    | Extened base maximum range to 1036384                      |
+---------+------------------------------------------------------------+
| 18.2    | Increase SRGB range to 400000                              |
+---------+------------------------------------------------------------+
| 18.3    | Increase SRGB lower-bound options and max range to 1000000 |
+---------+------------------------------------------------------------+
