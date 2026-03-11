services twamp
--------------

**Minimum user role:** operator

Two Way Active Measurement Protocol (TWAMP) is an open protocol. An open protocol allows different vendor equipment to work together without any additional proprietary equipment. TWAMP is used to measure network performance between two devices that support the TWAMP protocol by sending probe/data test packets between the devices. TWAMP uses a client-server architecture. There are two protocols used within TWAMP:

-	TWAMP-Control protocol - starts and ends test sessions. This runs between client and server

-	TWAMP - Test protocol - sends packets between two devices. This runs between session sender and session reflector

The TWAMP protocol sessions require two end-points with the following roles:

-	TWAMP client (typically used also as a session-sender)

	-	Control-client initiates, starts, and stops the TWAMP test sessions towards the TWAMP server.

	-	Session-sender creates TWAMP test packets which are sent to the session-reflector (TWAMP server) and collects and analyzes packets received.

-	TWAMP server, each NCE (typically used also as a session-reflector)

	-	Session-reflector returns a test packet when a packet is received from a session-sender. No information is stored but sent back to the client.

	-	Server manages one or more sessions with the TWAMP control-client and listens for control messages on a known TCP port.

DriveNets TWAMP implementation supports TWAMP clients, with the DriveNets NCE as the TWAMP server and Session-Reflector. As DriveNets TWAMP is in server mode, it only responds to sessions. This means no result or history information such as statistics are retained other than the counters which display the RX and TX packets. The counters can be seen by running the command show services twamp sessions in configuration mode. The TWAMP client aggregates all of the received measurement packets from all configured devices and analyzes the results for quality of control traffic, data sessions, jitter, or packet loss. TWAMP features include:

-	Test Packet Frequency - DriveNets TWAMP has a test packet frequency of 100 milliseconds continuously. The statistical distribution packets have an average inter-arrival delay of 3.3 milliseconds.

-	 DSCP Marking - supports, Class-of-Service (CoS), the DSCP value is the same as received by the client messages. This applies to both control packets and data packets.

-	Timestamps - Two timestamps are included in the reply message. The first is the time the packet is received on the ingress interface on the NCP and the second time-stamp refers to the time the packet leaves the NCP on the egress interface. In a standalone scheme the reply is transmitted from the same NCP, but in a cluster , the reply could be transmitted from another NCP within the cluster. The timestamps use the internal NTP clock within the system.

-	Scale- support up to ten simultaneous control sessions, which can be from the same client or different clients. Each control session can support up to ten simultaneous data sessions. This means that in total there can be up to 100 simultaneous data sessions.

To configure the the TWAMP responder (session-reflector) parameters, enter TWAMP configuration hierarchy:

**Command syntax: twamp**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)#


**Removing Configuration**

To revert all TWAMP configuration to default:
::

    dnRouter(cfg-srv)# no twamp

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 11.2    | Command introduced     |
+---------+------------------------+
| 17.0    | Added support for IPv6 |
+---------+------------------------+
