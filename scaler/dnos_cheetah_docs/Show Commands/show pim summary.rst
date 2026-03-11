show pim summary
----------------

**Minimum user role:** viewer

You can use this command to display the PIM summary information, which includes PIM states counters and PIM tree entry counters.


**Command syntax:show pim summary**

**Command mode:** operational


**Parameter table**

The following are the PIM state counters:

+---------------------------------+--------------------------------------------------------------------------+
| Parameter                       | Description                                                              |
+=================================+==========================================================================+
| PIM Tree (S,G)/( \*, G) Entries | The number of PIM Tree states                                            |
+---------------------------------+--------------------------------------------------------------------------+
| PIM MFIB Entries                | The number of PIM Tree states                                            |
+---------------------------------+--------------------------------------------------------------------------+
| Maximum Limit                   | The maximum allowed number of entries                                    |
+---------------------------------+--------------------------------------------------------------------------+
| Entries Threshold               | The number beyond which an alarm will be generated                       |
+---------------------------------+--------------------------------------------------------------------------+
| PIM Tree (S,G) replications     | The number of all output interfaces in PIM ( \*, G) and (S,G) tree states|
+---------------------------------+--------------------------------------------------------------------------+
| PIM Tree Entries Counters       | Per PIM Tree type entries counter                                        |
+---------------------------------+--------------------------------------------------------------------------+
| GR time                         | The amount of time stale PIM entries can be kept                         |
+---------------------------------+--------------------------------------------------------------------------+
| PIM NSR                         | The PIM NSR admin-state                                                  |
+---------------------------------+--------------------------------------------------------------------------+
| PIM Load-split                  | The PIM load-split admin-state                                           |
+---------------------------------+--------------------------------------------------------------------------+
| MoFRR UMH selection mode        | The MoFRR UMH selection mode                                             |
+---------------------------------+--------------------------------------------------------------------------+

**Example**
::

	dnRouter# show pim summary

	PIM Summary:  VRF:default
		Total PIM Tree entries                         :  32342
		Total PIM MFIB routes                          :  32564
		Maximum PIM MFIB entries limit                 :  60000
		PIM MFIB entries threshold                     :  40000
		PIM Tree total replications                    : 123092
	PIM Tree Entries Counters
		Number of (*,G/n) internal route entries       :      2
		Number of (*,G) route entries                  :   2000
		Number of (S,G)SSM route entries               :  10432
		Number of (S,G)SM route entries                :  10000
		Number of MoFRR protected entries              :  12
	Graceful-restart-time: 60 seconds
	PIM NSR: enabled
	PIM Load-split: enabled
	MoFRR UMH selection mode: non-ECMP-mode

.. **Help line:** Show PIM summary information

**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 12.0    | Command introduced             |
+---------+--------------------------------+
| 16.1    | Added support for PIM NSR      |
+---------+--------------------------------+
| 18.2.1  | Added PIM MFIB entries counter |
+---------+--------------------------------+
