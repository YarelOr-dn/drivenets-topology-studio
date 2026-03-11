show system ntp detail
----------------------

**Minimum user role:** viewer

To display NTP status details:



**Command syntax: show system ntp detail**

**Command mode:** operational



.. **Internal Note**

	- Command implementing "ntpq -nc rv <assid>" linux command

**Parameter table**

+------------+------------------------------------------------------------------------------------------------+
| Parameter  | Description                                                                                    |
+============+================================================================================================+
| status     | The system status consists of the following fields:                                            |
|            |                                                                                                |
|            | - Leap: displays the system leap indicator bits. See Table 1 below.                            |
|            |                                                                                                |
|            | - Source: displays the current synchronization sources. See Table 2 below.                     |
|            |                                                                                                |
|            | - Count: displays the number of events since the last time the code changed. See Table 3 below.|
+------------+------------------------------------------------------------------------------------------------+
| version    | NTP software version and build name                                                            |
+------------+------------------------------------------------------------------------------------------------+
| processor  | Hardware platform and version                                                                  |
+------------+------------------------------------------------------------------------------------------------+
| system     | Operating system and version                                                                   |
+------------+------------------------------------------------------------------------------------------------+
| leap       | Leap warning indicator (0-3)                                                                   |
+------------+------------------------------------------------------------------------------------------------+
| stratum    | Stratum (1-15)                                                                                 |
+------------+------------------------------------------------------------------------------------------------+
| precision  | Precision (log2 s)                                                                             |
+------------+------------------------------------------------------------------------------------------------+
| rootdelay  | Total roundtrip delay to the primary reference clock                                           |
+------------+------------------------------------------------------------------------------------------------+
| peer       | System peer association ID                                                                     |
+------------+------------------------------------------------------------------------------------------------+
| tc         | Time constant and poll exponent (log2(s)) (3-17)                                               |
+------------+------------------------------------------------------------------------------------------------+
| mintc      | Minimum time constant (log2(s)) (3-10)                                                         |
+------------+------------------------------------------------------------------------------------------------+
| clock      | Date and time of day                                                                           |
+------------+------------------------------------------------------------------------------------------------+
| refid      | Reference ID or kiss code. See Table 4 below.                                                  |
+------------+------------------------------------------------------------------------------------------------+
| reftime    | Reference time                                                                                 |
+------------+------------------------------------------------------------------------------------------------+
| offset     | Combined time offset                                                                           |
+------------+------------------------------------------------------------------------------------------------+
| sys_jitter | Combined system jitter                                                                         |
+------------+------------------------------------------------------------------------------------------------+
| frequency  | Clock frequency offset (PPM)                                                                   |
+------------+------------------------------------------------------------------------------------------------+
| clk_wander | Clock frequency wander (PPM)                                                                   |
+------------+------------------------------------------------------------------------------------------------+
| clk_jitter | Clock jitter                                                                                   |
+------------+------------------------------------------------------------------------------------------------+

The peer status parameters are:

+----------------+-------------------------------------------------------------------------------------------------+
| Parameter      | Description                                                                                     |
+================+=================================================================================================+
| status         | The system status consists of the following fields:                                             |
|                |                                                                                                 |
|                | - Status: displays the peer status code bits in hexadecimal. See Table 5 below.                 |
|                |                                                                                                 |
|                | - Select: displays the current selection status. See Table 6 below.                             |
|                |                                                                                                 |
|                | - Count: displays the number of events since the last time the code changed. See Table 7 below. |
+----------------+-------------------------------------------------------------------------------------------------+
| srcadr srcport | Source (remote) IP address and port                                                             |
+----------------+-------------------------------------------------------------------------------------------------+
| dstadr dstport | Destination (local) IP address and port                                                         |
+----------------+-------------------------------------------------------------------------------------------------+
| leap           | Leap indicator (0-3)                                                                            |
+----------------+-------------------------------------------------------------------------------------------------+
| stratum        | Stratum (1-15)                                                                                  |
+----------------+-------------------------------------------------------------------------------------------------+
| precision      | Precision (log2(s))                                                                             |
+----------------+-------------------------------------------------------------------------------------------------+
| rootdelay      | Total roundtrip delay to the primary reference clock                                            |
+----------------+-------------------------------------------------------------------------------------------------+
| rootdisp       | Total root dispersion to the primary reference clock                                            |
+----------------+-------------------------------------------------------------------------------------------------+
| refid          | Reference ID or kiss code. See Table 4 below.                                                   |
+----------------+-------------------------------------------------------------------------------------------------+
| reftime        | Reference time                                                                                  |
+----------------+-------------------------------------------------------------------------------------------------+
| reach          | Reach register (octal)                                                                          |
+----------------+-------------------------------------------------------------------------------------------------+
| unreach        | Unreach counter                                                                                 |
+----------------+-------------------------------------------------------------------------------------------------+
| hmode          | Host mode (1-6)                                                                                 |
+----------------+-------------------------------------------------------------------------------------------------+
| pmode          | Peer mode (1-5)                                                                                 |
+----------------+-------------------------------------------------------------------------------------------------+
| hpoll          | Host poll exponent (log2(s)) (3-17)                                                             |
+----------------+-------------------------------------------------------------------------------------------------+
| ppoll          | Peer poll exponent (log2(s)) (3-17)                                                             |
+----------------+-------------------------------------------------------------------------------------------------+
| headway        | Headway                                                                                         |
+----------------+-------------------------------------------------------------------------------------------------+
| flash          | The flash status displayed by the ntpq program rv command. See Table 8 below.                   |
+----------------+-------------------------------------------------------------------------------------------------+
| offset         | Filter offset                                                                                   |
+----------------+-------------------------------------------------------------------------------------------------+
| delay          | Filter delay                                                                                    |
+----------------+-------------------------------------------------------------------------------------------------+
| dispersion     | Filter dispersion                                                                               |
+----------------+-------------------------------------------------------------------------------------------------+
| jitter         | Filter jitter                                                                                   |
+----------------+-------------------------------------------------------------------------------------------------+
| bias           | Unicast/broadcast bias                                                                          |
+----------------+-------------------------------------------------------------------------------------------------+
| xleave         | Interleave delay (see NTP Interleaved Modes)                                                    |
+----------------+-------------------------------------------------------------------------------------------------+
| vrf            | vrf default (in-band management), vrf mgmt0 (out-of-band management)                            |
+----------------+-------------------------------------------------------------------------------------------------+

**Table 1 - Leap field**

Displays the system leap indicator bits coded as follows:

+------+--------------+-------------------------------------------------+
| Code | Message      | Description                                     |
+======+==============+=================================================+
| 0    | leap_none    | Normal synchronized state                       |
+------+--------------+-------------------------------------------------+
| 1    | leap_add_sec | Insert second after 23:59:59 of the current day |
+------+--------------+-------------------------------------------------+
| 2    | leap_del_sec | Delete second 23:59:59 of the current day       |
+------+--------------+-------------------------------------------------+
| 3    | leap_alarm   | Never synchronized                              |
+------+--------------+-------------------------------------------------+

**Table 2 - Source field**

Displays the current synchronization source coded as follows:

+------+-----------------+----------------------------------------------+
| Code | Message         | Description                                  |
+======+=================+==============================================+
| 0    | sync_unspec     | Not yet synchronized                         |
+------+-----------------+----------------------------------------------+
| 1    | sync_pps        | Pulse-per-second signal (Cs, Ru, GPS, etc.)  |
+------+-----------------+----------------------------------------------+
| 2    | sync_lf_radio   | VLF/LF radio (WWVB, DCF77, etc.)             |
+------+-----------------+----------------------------------------------+
| 3    | sync_hf_radio   | MF/HF radio (WWV, etc.)                      |
+------+-----------------+----------------------------------------------+
| 4    | sync_uhf_radio  | VHF/UHF radio/satellite (GPS, Galileo, etc.) |
+------+-----------------+----------------------------------------------+
| 5    | sync_local      | Local timecode (IRIG, LOCAL driver, etc.)    |
+------+-----------------+----------------------------------------------+
| 6    | sync_ntp        | NTP                                          |
+------+-----------------+----------------------------------------------+
| 7    | sync_other      | Other (IEEE 1588, openntp, crony, etc.)      |
+------+-----------------+----------------------------------------------+
| 8    | sync_wristwatch | Eyeball and wristwatch                       |
+------+-----------------+----------------------------------------------+
| 9    | sync_telephone  | Telephone modem (ACTS, PTB, etc.)            |
+------+-----------------+----------------------------------------------+

**Table 3 - Count field**

Displays the number of events since the last time the code changed. Upon reaching 15, subsequent events with the same code are ignored. The Event Field displays the most recent event message coded as follows:

+------+-------------------------+----------------------------------------+
| Code | Message                 | Description                            |
+======+=========================+========================================+
| 00   | unspecified             | Unspecified                            |
+------+-------------------------+----------------------------------------+
| 01   | freq_not_set            | Frequency file not available           |
+------+-------------------------+----------------------------------------+
| 02   | freq_set                | Frequency set from frequency file      |
+------+-------------------------+----------------------------------------+
| 03   | spike_detect            | Spike detected                         |
+------+-------------------------+----------------------------------------+
| 04   | freq_mode               | Initial frequency training mode        |
+------+-------------------------+----------------------------------------+
| 05   | clock_sync              | Clock synchronized                     |
+------+-------------------------+----------------------------------------+
| 06   | restart                 | Program restart                        |
+------+-------------------------+----------------------------------------+
| 07   | panic_stop              | Clock error more than 600 s            |
+------+-------------------------+----------------------------------------+
| 08   | no_system_peer          | No system peer                         |
+------+-------------------------+----------------------------------------+
| 09   | leap_armed              | Leap second armed from file or Autokey |
+------+-------------------------+----------------------------------------+
| 0a   | leap_disarmed           | Leap second disarmed                   |
+------+-------------------------+----------------------------------------+
| 0b   | leap_event              | Leap event                             |
+------+-------------------------+----------------------------------------+
| 0c   | clock_step              | Clock stepped                          |
+------+-------------------------+----------------------------------------+
| 0d   | kern                    | Kernel information message             |
+------+-------------------------+----------------------------------------+
| 0e   | TAI...                  | Leapsecond values update from file     |
+------+-------------------------+----------------------------------------+
| 0f   | stale leapsecond values | New NIST leapseconds file needed       |
+------+-------------------------+----------------------------------------+
| 10   | clockhop                | Spurious clock hop suppressed          |
+------+-------------------------+----------------------------------------+

**Table 4 - Kiss code**

Used in kiss-o'-death (koD) packets, billboard displays and log messages. They consist of a string of four zero-padded ASCII charactes. In practice they are informal and tend to change with time and implementation. Following is the current list:

+-------+-------------------------+
| Code  | Description             |
+=======+=========================+
| ACST  | Manycast server         |
+-------+-------------------------+
| AUTH  | Authentication error    |
+-------+-------------------------+
| AUTO  | Autokey sequence error  |
+-------+-------------------------+
| BCST  | Broadcast server        |
+-------+-------------------------+
| CRYPT | Autokey protocol error  |
+-------+-------------------------+
| DENY  | Access denied by server |
+-------+-------------------------+
| INIT  | Association initialized |
+-------+-------------------------+
| MCST  | Multicast server        |
+-------+-------------------------+
| RATE  | Rate exceeded           |
+-------+-------------------------+
| TIME  | Association timeout     |
+-------+-------------------------+
| STEP  | Step time change        |
+-------+-------------------------+

**Table 5 - Status field**

Displays the peer status code bits in hexadecimal as follows:

+------+---------+------------------------+
| Code | Message | Description            |
+======+=========+========================+
| 08   | bcst    | Broadcast association  |
+------+---------+------------------------+
| 10   | reach   | Host reachable         |
+------+---------+------------------------+
| 20   | authenb | Authentication enabled |
+------+---------+------------------------+
| 40   | auth    | Authentication OK      |
+------+---------+------------------------+
| 80   | config  | Persistent association |
+------+---------+------------------------+

**Table 6 - Select field**

Displays the current selection. status The T Field displays the tally codes beginning the ntpq peers display. The values are coded as follows:

+------+---------------+----+--------------------------------------------+
| Code | Message       | T  | Description                                |
+======+===============+====+============================================+
| 0    | sel_reject    |    | Discarded as not valid (TEST10-TEST13)     |
+------+---------------+----+--------------------------------------------+
| 1    | sel_falsetick | x  | Discarded by intersection algorithm        |
+------+---------------+----+--------------------------------------------+
| 2    | sel_excess    | .  | Discarded by table overflow (not used)     |
+------+---------------+----+--------------------------------------------+
| 3    | sel_outlyer   | \- | Discarded by the cluster algorithm         |
+------+---------------+----+--------------------------------------------+
| 4    | sel_candidate | +  | Included by the combine algorithm          |
+------+---------------+----+--------------------------------------------+
| 5    | sel_backup    | #  | Backup (more than tinker maxclock sources) |
+------+---------------+----+--------------------------------------------+
| 6    | sel_sys.peer  | *  | System peer                                |
+------+---------------+----+--------------------------------------------+
| 7    | sel_pps.peer  | o  | PPS peer (when the prefer peer is valid)   |
+------+---------------+----+--------------------------------------------+

**Table 7 - Count field (peer status)**

Displays the number of events since the last time the code changed. Upon reaching 15, subsequent events with the same code are ignored. The Event Field displays the most recent event message coded as follows:

+------+------------------+--------------------------------------+
| Code | Message          | Description                          |
+======+==================+======================================+
| 01   | mobilize         | Association mobilized                |
+------+------------------+--------------------------------------+
| 02   | demobilize       | Association demobilized              |
+------+------------------+--------------------------------------+
| 03   | unreachable      | Server unreachable                   |
+------+------------------+--------------------------------------+
| 04   | reachable        | Server reachable                     |
+------+------------------+--------------------------------------+
| 05   | restart          | Association restart                  |
+------+------------------+--------------------------------------+
| 06   | no_reply         | No server found (ntpdate mode)       |
+------+------------------+--------------------------------------+
| 07   | rate_exceeded    | Rate exceeded (kiss code RATE)       |
+------+------------------+--------------------------------------+
| 08   | access_denied    | Access denied (kiss code DENY)       |
+------+------------------+--------------------------------------+
| 09   | leap_armed       | Leap armed from server LI code       |
+------+------------------+--------------------------------------+
| 0a   | sys_peer         | Become system peer                   |
+------+------------------+--------------------------------------+
| 0b   | clock_event      | See clock status word                |
+------+------------------+--------------------------------------+
| 0c   | bad_auth         | Authentication failure               |
+------+------------------+--------------------------------------+
| 0d   | popcorn          | Popcorn spike suppressor             |
+------+------------------+--------------------------------------+
| 0e   | interleave_mode  | Entering interleave mode             |
+------+------------------+--------------------------------------+
| 0f   | interleave_error | Interleave error (recovered)         |
+------+------------------+--------------------------------------+
| 10   | TAI...           | Leapsecond values update from server |
+------+------------------+--------------------------------------+

**Table 8 - Flash status**

Displayed by the ntpq program rv command. It consists of a number of bits coded in hexadecimal as follows:

+------+--------+--------------+---------------------------+
| Code | Tag    | Message      | Description               |
+======+========+==============+===========================+
| 0001 | TEST1  | pkt_dup      | Duplicate packet          |
+------+--------+--------------+---------------------------+
| 0002 | TEST2  | pkt_bogus    | Bogus packet              |
+------+--------+--------------+---------------------------+
| 0004 | TEST3  | pkt_unsync   | Protocol unsynchronized   |
+------+--------+--------------+---------------------------+
| 0008 | TEST4  | pkt_denied   | Access denied             |
+------+--------+--------------+---------------------------+
| 0010 | TEST5  | pkt_auth     | Bad authentication        |
+------+--------+--------------+---------------------------+
| 0020 | TEST6  | pkt_stratum  | Bad synch or stratum      |
+------+--------+--------------+---------------------------+
| 0040 | TEST7  | pkt_header   | Bad header                |
+------+--------+--------------+---------------------------+
| 0080 | TEST8  | pkt_autokey  | Bad autokey               |
+------+--------+--------------+---------------------------+
| 0100 | TEST9  | pkt_crypto   | Bad crypto                |
+------+--------+--------------+---------------------------+
| 0200 | TEST10 | peer_stratum | Peer bad synch or stratum |
+------+--------+--------------+---------------------------+
| 0400 | TEST11 | peer_dist    | Peer distance exceeded    |
+------+--------+--------------+---------------------------+
| 0800 | TEST12 | peer_loop    | Peer synchronization loop |
+------+--------+--------------+---------------------------+
| 1000 | TEST13 | peer_unreach | Peer unreachable          |
+------+--------+--------------+---------------------------+

**Example**
::

	dnRouter# show system ntp detail

	Local clock status:

	status=0615 leap_none, sync_ntp, 1 event, clock_sync,
	version="ntpd 4.2.6p5@1.2349-o Wed Jul 12 12:22:58 UTC 2017 (1)",
	processor="x86_64", system="Linux/4.4.0-57-generic", leap=00, stratum=3,
	precision=-23, rootdelay=81.967, rootdisp=110.026, refid=91.189.89.198,
	reftime=de369477.c054f21a  Tue, Feb 20 2018 12:35:03.751,
	clock=de3697ee.c0799173  Tue, Feb 20 2018 12:49:50.751, peer=40962,
	tc=10, mintc=3, offset=-2.937, frequency=-13.845, sys_jitter=2.066,
	clk_jitter=1.971, clk_wander=0.187


	Peers status:

	vrf=default,status=9417 conf, reach, sel_candidate, 1 event, rate_exceeded,
	srcadr=109.226.40.40, srcport=123, dstadr=100.64.2.118, dstport=123,
	leap=00, stratum=2, precision=-24, rootdelay=184.906, rootdisp=68.909,
	refid=132.163.96.4,
	reftime=de3688be.6662edb0  Tue, Feb 20 2018 11:45:02.399,
	rec=de3693e4.feec140c  Tue, Feb 20 2018 12:32:36.995, reach=377,
	unreach=0, hmode=3, pmode=4, hpoll=10, ppoll=10, headway=3751,
	flash=00 ok, keyid=0, offset=-0.605, delay=7.238, dispersion=18.988,
	jitter=2.033, xleave=0.027,
	filtdelay== 11.98 7.24 6.44 15.45 7.24 6.45 6.45 7.24?,
	filtoffset== -3.10 -0.60 0.01 3.85 0.04 0.44 0.36 -0.46?,
	filtdisp== 0.00 15.69 31.11 46.67 62.60 78.08 93.89 109.55?



	vrf=default, status=965a conf, reach, sel_sys.peer, 5 events, sys_peer,
	srcadr=91.189.89.198, srcport=123, dstadr=100.64.2.118, dstport=123,
	leap=00, stratum=2, precision=-24, rootdelay=8.133, rootdisp=34.454,
	refid=145.238.203.14,
	reftime=de368fcf.f1f76ec2  Tue, Feb 20 2018 12:15:11.945,
	rec=de369478.0ebf63d4  Tue, Feb 20 2018 12:35:04.057, reach=357,
	unreach=0, hmode=3, pmode=4, hpoll=10, ppoll=10, headway=0, flash=00 ok,
	keyid=0, offset=-4.143, delay=73.834, dispersion=16.296, jitter=5.619,
	xleave=0.029,
	filtdelay== 73.83 75.08 63.87 66.85 62.75 64.85 67.92 75.35?,
	filtoffset== -4.14 -5.62 1.11 3.78 2.54 1.44 0.31 1.60?,
	filtdisp== 0.00 15.93 32.01 47.54 79.31 95.57 111.59 127.20?

.. **Help line:** show ntp status detail

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+


