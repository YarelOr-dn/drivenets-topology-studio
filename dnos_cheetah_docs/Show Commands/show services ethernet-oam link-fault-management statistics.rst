show services ethernet-oam link-fault-management statistics
-----------------------------------------------------------

**Minimum user role:** viewer

To display the ethernet OAM link fault management message statistics:


**Command syntax: show services ethernet-oam link-fault-management statistics** [interface-name]

**Command mode:** operational



**Note**

- The 'show services ethernet-oam link-fault-management statistics' command is used to display a summary of ethernet OAM LFM protocol statistics for all interfaces.

- The 'show services ethernet-oam link-fault-management statistics [interface-name]' command is used to display detailed ethernet OAM LFM protocol statistics for a specific interface.


**Parameter table**

+----------------+-----------------------------------------------------------------------+---------------------------------------+---------+
| Parameter      | Description                                                           | Range                                 | Default |
+================+=======================================================================+=======================================+=========+
| interface-name | Display detailed ethernet OAM LFM statistics for a specific interface | ge<interface speed>-<A>/<B>/<C>       | \-      |
+----------------+-----------------------------------------------------------------------+---------------------------------------+---------+

The following describes the parameters in the table:

+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Parameter                                 | Description                                                                                |
+===========================================+============================================================================================+
| Information OAMPDU TX                     | Number of OAM PDUs transmitted                                                             |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Information OAMPDU RX                     | Number of OAM PDUs received                                                                |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Unique Event Notification OAMPDU TX       | Number of unique event notification OAM PDUs transmitted                                   |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Duplicate Event Notification OAMPDU TX    | Number of duplicate event notification OAM PDUs transmitted                                |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Unique Event Notification OAMPDU RX       | Number of unique event notification OAM PDUs received                                      |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Duplicate Event Notification OAMPDU RX    | Number of duplicate event notification OAM PDUs received                                   |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Loopback Control OAMPDU TX                | Number of loopback control OAM PDUs transmitted                                            |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Loopback Control OAMPDU RX                | Number of loopback control OAM PDUs received                                               |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| MIB Variable Retrieval Request OAMPDU TX  | Number of OAM PDUs sent to request MIB objects on a remote device                          |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| MIB Variable Retrieval Request OAMPDU RX  | Number of OAM PDUs received and requesting MIB objects on a local device                   |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| MIB Variable Retrieval Response OAMPDU TX | Number of OAM PDUs sent by the local device in response to a request from a remote device  |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| MIB Variable Retrieval Response OAMPDU RX | Number of OAM PDUs sent by the remote device in response to a request from a local device  |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Organization Specific OAMPDU TX           | Number of DriveNets specific OAM PDUs sent                                                 |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Organization Specific OAMPDU RX           | Number of DriveNets specific OAM PDUs received                                             |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Unsupported OAMPDU TX                     | Number of unsupported OAM PDUs sent                                                        |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Unsupported OAMPDU RX                     | Number of unsupported OAM PDUs received                                                    |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Frames lost due to OAM                    | Number of frames discarded by the OAM client                                               |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Adjacency Loss events                     | Number of times an OAM session has dropped                                                 |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Link Fault events                         | Number of link fault events transmitted or received                                        |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Dying Gasp events                         | Number of dying gasp events transmitted or received                                        |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Critical Error events                     | Number of critical error events transmitted or received                                    |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Errored Symbol Period events              | Number of errored symbol period events transmitted or received                             |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Errored Frame events                      | Number of errored frame events transmitted or received                                     |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Errored Frame Period events               | Number of errored frame period events transmitted or received                              |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Errored Frame Seconds Summary events      | Number of errored frame seconds summary events transmitted or received                     |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Errors in last window                     | Number of errors in the window of the last reported link event                             |
+-------------------------------------------+--------------------------------------------------------------------------------------------+
| Total errors                              | The total number of errors reported for the specific link event                            |
+-------------------------------------------+--------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show services ethernet-oam link-fault-management statistics

	| Interface    | Session State  | Information PDU TX | Information PDU RX | Event Notification PDU TX | Event Notification PDU RX | Loopback Control PDU TX | Loopback Control PDU RX | Frames Lost due to OAM |
	+--------------+----------------+--------------------+--------------------+---------------------------+---------------------------+-------------------------+-------------------------+------------------------+
	| ge100-0/0/0  | PASSIVE_WAIT   | 0                  | 0                  | 0                         | 0                         | 0                       | 0                       | 0                      |
	| ge100-0/0/19 | SEND_ANY       | 0                  | 0                  | 0                         | 0                         | 0                       | 0                       | 0                      |
	| ge100-0/0/28 | INACTIVE       | 0                  | 0                  | 0                         | 0                         | 0                       | 0                       | 0                      |


	dnRouter# show services ethernet-oam link-fault-management statistics ge100-0/0/19

	Interface: ge100-0/0/0

	Session state: SEND_ANY

	Counters:
		OAMPDUs:
			Information OAMPDU TX:                           217
			Information OAMPDU RX:                           186
			Unique Event Notification OAMPDU TX:               0
			Duplicate Event Notification OAMPDU TX:            0
			Unique Event Notification OAMPDU RX:               9
			Duplicate Event Notification OAMPDU RX:            0
			Organization Specific OAMPDU TX:                   0
			Organization Specific OAMPDU RX:                   0
			Unsupported OAMPDU RX:                             0
			Frames Lost due to OAM:                           23

		Local faults and events:
			Adjacency Loss events:                             0
			Link Fault events:                                 0
			Dying Gasp events:                                 0
			Critical Error events:                             0
			Errored Symbol Period events:                      0
				Errors in last window:                         0
				Total errors:                                  0
			Errored Frame events:                              0
				Errors in last window:                         0
				Total errors:                                  0
			Errored Frame Period events:                       0
				Errors in last window:                         0
				Total errors:                                  0
			Errored Frame Second events:                       0
				Errors in last window:                         0
				Total errors:                                  0

		Remote faults and events:
			Link Fault events:                                 0
			Dying Gasp events:                                 0
			Critical Error events:                             0
			Errored Symbol Period events:                      0
				Errors in last window:                         0
				Total errors:                                  0
			Errored Frame events:                              0
				Errors in last window:                         0
				Total errors:                                  0
			Errored Frame Period events:                       0
				Errors in last window:                         0
				Total errors:                                  0
			Errored Frame Second events:                       0
				Errors in last window:                         0
				Total errors:                                  0


.. **Help line:** Show 802.3ah Ethernet OAM LFM statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
