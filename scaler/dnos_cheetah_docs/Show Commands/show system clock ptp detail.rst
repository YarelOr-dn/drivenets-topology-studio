show system clock ptp detail
----------------------------

**Minimum user role:** viewer

To display detailed information of the PTP clock in a single view:

**Command syntax: show system clock ptp detail** [node-name] [node-id]

**Command mode:** operational

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter | Description                                                                                                                                | Range              |
+===========+============================================================================================================================================+====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP                |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..191        |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Note**
- When the PTP feature is disabled or node is not in an operational state, data will not be available.

.. - By default (if node name not specified), output will show all the nodes in DNOS cluster.
.. - In Standalone mode, control ports are named ctrl-ncc-0/[0-1] and not ctrl-ncp-X/Y.

**Example**
::

	dnRouter# show system clock ptp detail ncp 0

	PTP Clock Default dataset parameters:
		Mode:                            enabled
		Type:                            T-BC
		Profile:                         G.8275.1
		Identity:                        04:05:AA:FE:EF:08:9A:00
		Num-of-ports:                    2
		Domain:                          24
		Class:                           0xFF
		Local priority:                  128
		Priority-2:                      128
		Max steps removed:               20
		Holdover-in-spec time:           120 minutes
		Num-of-steps:                    1
		Accuracy:                        0xFE
		Offset Scaled Log Variance:      0xFFFF

	Synchronous Ethernet configuration:
	    Mode:  enabled
	    DPLL ref clock state: locked
	    Quality level: ql_prc
	    Active source name: ge400-0/0/1
	    Active source alarm raised: false

	PTP Clock Current dataset parameters:
		Steps removed:	                 3
		Offset from master:              3 nsec
		Mean path delay:                 1 nsec

	1pps SMB port mode:                  output

	PTP Clock Parent dataset parameters:
		Identity:                 12:B:BB:FB:1F:28:1A:11
		Port number:              2
		GM identity:              D4:05:AA:FE:EF:08:9A:01
		GM clock class:           6
		GM clock accuracy:        0xFE
		GM offset-log-variance:   0xFFFF
		GM priority-2:            128

	PTP Clock time-properties dataset parameters:
		ToD:                      Thu Sep 1 15:23:55 2022
		Time source:              GPS
		Current UTC offset:       1 sec
		Current UTC offset valid: True
		Leap59:                   False
		Leap61:                   False
		Time traceable:           False
		Frequency traceable:      False
		PTP timescale:            True

	PTP clock statistics:
		State:                   enabled
		Received packets:        128
		Sent packets:            256
		Discarded packets:       3
		L2 received packets:     48
		Receive queue overflows: 2

	PTP Clock Master ports:
		| Interface name     | Port number |
		|--------------------+-------------|
        | ge400-0/0/0        | 1           |
        | ge400-0/0/10       | 2           |
        | ge400-0/0/12       | 5           |

	PTP Clock Slave ports:
		| Interface name     | Port number |
		|--------------------+-------------|
        | ge400-0/0/3        | 3           |
        | ge400-0/0/18       | 4           |
        | ge400-0/0/22       | 6           |

	dnRouter# show system clock ptp detail

	ncp 0 (dn-ncp-0)

		PTP Clock Default dataset parameters:
			Mode:                            enabled
			Type:                            T-BC
			Profile:                         G.8275.1
			Identity:                        04:05:AA:FE:EF:08:9A:00
			Num-of-ports:                    6
			Domain:                          24
			Class:                           0xFF
			Local priority:                  128
			Priority-2:                      128
			Max steps removed:               20
			Holdover-in-spec time:           120 minutes
			Num-of-steps:                    1
			Accuracy:                        0xFE
			Offset Scaled Log Variance:      0xFFFF

		Synchronous Ethernet configuration:
		    Mode:  enabled
		    DPLL ref clock state: locked
		    Quality level: ql_prc
		    Active source name: ge400-0/0/2
		    Active source alarm raised: true (alarm reason: esmc-to)

		PTP Clock Current dataset parameters:
			Steps removed:	                 3
			Offset from master:              3 nsec
			Mean path delay:                 1 nsec

		1pps SMB port mode:                  output

		PTP Clock Parent dataset parameters:
			Identity:                 12:B:BB:FB:1F:28:1A:11
			Port number:              2
			GM identity:              D4:05:AA:FE:EF:08:9A:01
			GM clock class:           6
			GM clock accuracy:        0xFE
			GM offset-log-variance:   0xFFFF
			GM priority-2:            128

		PTP Clock time-properties dataset parameters:
			ToD:                  Thu Sep 1 15:23:55 2022
			Time source:              GPS
			Current UTC offset:       1 sec
			Current UTC offset valid: True
			Leap59:                   False
			Leap61:                   False
			Time traceable:           False
			Frequency traceable:      False
			PTP timescale:            True

		PTP clock statistics:
			Received packets:        128
			Sent packets:            256
			Discarded packets:       3
			L2 received packets:     48
			Receive queue overflows: 2

		PTP Clock Master ports:
			| Interface name     | Port number |
			|--------------------+-------------|
			| ge400-0/0/0        | 1           |
			| ge400-0/0/10       | 2           |
			| ge400-0/0/12       | 5           |

		PTP Clock Slave ports:
			| Interface name     | Port number |
			|--------------------+-------------|
			| ge400-0/0/3        | 3           |
			| ge400-0/0/18       | 4           |
			| ge400-0/0/22       | 6           |


	ncp 1 (dn-ncp-1)

		PTP Clock Default dataset parameters:
			Mode:                            enabled
			Type:                            T-TSC
			Profile:                         G.8275.1
			Identity:                        14:15:2A:3E:4F:08:9A:00
			Num-of-ports:                    2
			Domain:                          24
			Class:                           0xFF
			Local priority:                  128
			Priority-2:                      128
			Max steps removed:               20
			Holdover-in-spec time:           120 minutes
			Num-of-steps:                    1
			Accuracy:                        0xFE
			Offset Scaled Log Variance:      0xFFFF

		Synchronous Ethernet configuration:
		    Mode:  disabled
		    DPLL ref clock state:
		    Quality level:
		    Active source name:
		    Active source alarm raised:

		PTP Clock Current dataset parameters:
			Steps removed:	                 4
			Offset from master:              2 nsec
			Mean path delay:                 2 nsec

		1pps SMB port mode:                  disabled

		PTP Clock Parent dataset parameters:
			Identity:                 22:2B:2B:2B:2F:28:1A:11
			Port number:              1
			GM identity:              D4:05:AA:FE:EF:08:9A:01
			GM clock class:           6
			GM clock accuracy:        0xFE
			GM offset-log-variance:   0xFFFF
			GM priority-2:            128

		PTP Clock time-properties dataset parameters:
			ToD:                  Thu Sep 1 15:23:55 2022
			Time source:              PTP
			Current UTC offset:       1 sec
			Current UTC offset valid: True
			Leap59:                   False
			Leap61:                   False
			Time traceable:           False
			Frequency traceable:      False
			PTP timescale:            True

		PTP clock statistics:
			Received packets:        128
			Sent packets:            256
			Discarded packets:       31
			L2 received packets:     48
			Receive queue overflows: 0

		PTP Clock Master ports:      N/A

		PTP Clock Slave ports:
			| Interface name     | Port number |
			|--------------------+-------------|
			| ge400-0/0/30       | 2           |
			| ge400-0/0/1        | 4           |

**Example**
::

    dnRouter# show system clock ptp

        Requested data is unavailable.

.. **Help line:** Display PTP clock detailed information

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
