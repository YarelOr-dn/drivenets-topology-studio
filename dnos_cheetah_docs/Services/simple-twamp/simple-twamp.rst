services simple-twamp
---------------------

**Minimum user role:** operator

The Simple Two Way Active Measurement Protocol (STAMP) is an open protocol. An open protocol allows different vendor equipment to work together without any additional proprietary equipment. STAMP is used as a lightweight implementation of the TWAMP protocol to measure network performance between two devices that support the TWAMP-Test protocol by sending probe/data test packets between a session sender and a session reflector, without the need for TWAMP-Control protocol which makes it more scalable.

Unlike standard track TWAMP, Simple TWAMP - Test protocol - sends packets between two devices. This runs between session sender and session reflector

The Simple TWAMP protocol sessions require two end-points with the following roles:

	-	Session-sender - creates TWAMP test packets which are sent to the session-reflector and collects and analyzes packets received.

	-	Session-reflector - returns a test packet when a packet is received from a session-sender. No information is stored but sent back to the session-sender.

DriveNets Simple TWAMP implementation supports both roles of Session-Sender and Session-Reflector:

- As a Session-Reflector DriveNets devices only responds to sessions. This means no result or history information such as statistics are retained other than the counter which displays the reflected packets. The counters can be seen by running the command show services performance-monitoring sessions.

- As a Session-Sender DriveNets aggregates all of the received measurement packets from all configured devices and analyzes the results for quality of data sessions, delay, jitter, or packet loss.

Simple TWAMP features include:

-	DSCP Marking - supports Class-of-Service (CoS) in two modes, either the DSCP value of reflected packets is remarked per configuration or it can be reflected with the same DSCP value received by the Session-Sender.

-	Timestamps - Two timestamps are included in the reply message. The first is the time the packet is received on the ingress interface on the NCP and the second time-stamp refers to the time the packet leaves the NCP on the egress interface. In a standalone scheme the reply is transmitted from the same NCP, but in a cluster , the reply could be transmitted from another NCP within the cluster. The timestamps use the internal NTP clock within the system.

-	Scale - support up to 2K simultaneous test sessions, which can be from the same Session-Sender or different Session-Senders.


To enter the Simple TWAMP configuration hierarchy:

**Command syntax: simple-twamp**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)#


**Removing Configuration**

To revert all Simple TWAMP configuration to default:
::

    dnRouter(cfg-srv)# no simple-twamp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
