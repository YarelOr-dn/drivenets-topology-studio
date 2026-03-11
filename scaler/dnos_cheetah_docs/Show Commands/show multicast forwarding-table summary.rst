show multicast forwarding-table summary
---------------------------------------

**Minimum user role:** viewer

You can use this command to display the multicast forwarding-table summary information. Information can be displayed from a specific NCP. By default, information is displayed from an active NCP with a minimum ID.

**Command syntax: show multicast forwarding-table summary** ncp [ncp-id]

**Command mode:** operational



.. **Note**

	- If NCP is disconnecetd or not reachable, output will show "NCP x not connected"
  .. - For NCP3 which contains two chips, actual replications will be displayed per each unit. Replications threshold and maximum limit apply to each each unit separately.

**Parameter table**

+-----------+-------------------------------------+--------+---------------+
| Parameter | Description                         | Range  | Default       |
+===========+=====================================+========+===============+
| ncp-id    | The ID of the specific NCP (string) | 0..191 | Lowest NCP ID |
+-----------+-------------------------------------+--------+---------------+

**Example**
::

	dnRouter# show multicast forwarding-table summary

	VRF: default
	NCP-ID: 0

   	Multicast forwarding-table summary
		Number of (*,G,*) forwarding entries                        : 234
		Number of (*,G,*), RPF(cpu) forwarding entries              : 462
		Number of (*,G,*), RPF(in-lif) forwarding entries           : 3462
		Number of (S,G,*), RPF(in-lif) forwarding entries           : 23454
		Number of (S,G,in-lif) inform entries                       : 4321
		Number of (S,G,in-lif) MoFRR protecting entries             : 981
		Number of (*,G/n,*) range drop entries                      : 1
		Number of (*,G/n,*) range punted entries                    : 9

	Actual Multicast (S,G) replications	:   123092
	Maxinum (S,G) replications limit	:   256000
	(S,G) replications threshold		:   192000


	dnRouter# show multicast forwarding-table summary ncp 3

	NCP 3 not connected



	dnRouter# show multicast forwarding-table summary ncp 12

	VRF: default
	NCP-ID: 12

   	Multicast forwarding-table summary
		Number of (*,G,*) forwarding entries                        : 234
		Number of (*,G,*), RPF(cpu) forwarding entries              : 462
		Number of (*,G,*), RPF(in-lif) forwarding entries           : 3462
		Number of (S,G,*), RPF(in-lif) forwarding entries           : 23454
		Number of (S,G,in-lif) inform entries                       : 4321
		Number of (S,G,in-lif) MoFRR protecting entries             : 981
		Number of (*,G/n,*) range drop entries                      : 1
		Number of (*,G/n,*) range punted entries                    : 9

	Actual Multicast (S,G) replications in unit 0   :   123092
	Actual Multicast (S,G) replications in unit 1   :   87612
	Maxinum (S,G) replications limit                :   256000
	(S,G) replications threshold                    :   192000

.. **Help line:** Show Multicast forwarding-table summary

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 12.0    | Command introduced                                            |
+---------+---------------------------------------------------------------+
| 13.0    | Updated ncp-id range                                          |
+---------+---------------------------------------------------------------+
| 14.0    | Updated MoFRR support                                         |
+---------+---------------------------------------------------------------+
| 16.1    | Updated output to show actual multicast replications per unit |
+---------+---------------------------------------------------------------+
