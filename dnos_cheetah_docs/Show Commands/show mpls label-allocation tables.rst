show mpls label-allocation tables
---------------------------------

**Minimum user role:** viewer

This command displays MPLS label block allocation for each routing protocol. Each protocol allocates labels from a defined label block when the process starts.

To display the MPLS label allocations:

**Command syntax: show mpls label-allocation tables**

**Command mode:** operational



**Note**

- Only segment-routing label blocks are configurable. Other protocols derive their label block from the segment-routing configured values.

..
	- When the configured values differ from the in use values the following line will be printed "Configured values differ from current in use values, restart system to apply new values."

	- Only  SR label blocks are configurable by user, other protocol derive their label block according to SR configured values

**Parameter table**

+------------+-----------------------------------------------------------------------------------------------------------------+
| Parameter  | Description                                                                                                     |
+============+=================================================================================================================+
| In use     | Displays the currently used label blocks.                                                                       |
+------------+-----------------------------------------------------------------------------------------------------------------+
| Configured | Displays the configured label blocks for the protocol. The configured value becomes in use after system restart |
+------------+-----------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show mpls label-allocation tables
	In use:
	| Protocol   | Total labels | label ranges                            |
	|------------+--------------+-----------------------------------------+
	| ldp        |        59302 | 20001-69999                             |
	| rsvp       |        39534 | 16-7999, 52000-59999, 68001-91549       |
	| bgp        |       889531 | 100001-799999                           |
	| bgp-vrf    |         8192 | 1040384-1048575                         |
	| srgb       |        32000 | 20000-51999                             |
	| srlb       |         8000 | 8000-15999                              |

    Configured:
    Configured values differ from current in use values, restart system to apply new values.
	| Protocol   | Total labels | label ranges                            |
	|------------+--------------+-----------------------------------------+
	| ldp        |        48382 | 266270-314651                           |
	| rsvp       |        32254 | 16-15999, 250000-266269                 |
	| bgp        |       725732 | 314652-1040383                          |
	| bgp-vrf    |         8192 | 1040384-1048575                         |
	| srgb       |       220000 | 30000-249999                            |
	| srlb       |         8000 | 16000-23999                             |
	
.. **Help line:** displays mpls label block allocation

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 11.2    | Command introduced                              |
+---------+-------------------------------------------------+
| 11.4    | Command not supported                           |
+---------+-------------------------------------------------+
| 13.0    | Command reintroduced                            |
+---------+-------------------------------------------------+
| 14.0    | Added segment-routing information in the output |
+---------+-------------------------------------------------+


