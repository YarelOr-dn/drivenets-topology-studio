routing-options segment-routing mpls global-block
-------------------------------------------------

**Minimum user role:** operator

The segment routing global block (SRGB) is a set of labels that are reserved for segment routing and have global significance in the routing protocol domain.

The configured label block is reserved even if not used by any of the segment-routing capable protocols.

By default, the segment-routing capable protocols use the SRGB/SRLB range configured under the routing-options hierarchy level, unless a specific block is configured under the protocol level.

To configure the segment routing global block (SRGB) used by the router:

**Command syntax: global-block [base] [range]**

**Command mode:** config

**Hierarchies**

- routing-options segment-routing mpls

**Note**

- When changing the configuration, the new block will only apply on the next system restart. To view the configured labels blocks and the currently in used label blocks, use the show mpls label-allocation tables command.

- The base and range together define the block size (i.e. the number of labels in the block) and must be identical for all instances, even if segment-routing is disabled.

- SRGB and SRLB blocks must not overlap.

.. - SRGB and SRLB blocks must not overlap

	- 'no' command returns to default value

**Parameter table**

+-----------+---------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                         | Range        | Default |
+===========+=====================================================================+==============+=========+
| base      | The first MPLS label value (SID) in the SRGB range.                 | 16..1036384  | 16000   |
+-----------+---------------------------------------------------------------------+--------------+---------+
| range     | The number of label values from the base till the end of the block. | 4000..400000 | 8000    |
+-----------+---------------------------------------------------------------------+--------------+---------+

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

.. **Help line:** configure router srgb

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 14.0    | Command introduced                      |
+---------+-----------------------------------------+
| 16.1    | Exteneded base maximum range to 1036384 |
+---------+-----------------------------------------+
| 18.2    | Increased SRGB range to 400000          |
+---------+-----------------------------------------+
