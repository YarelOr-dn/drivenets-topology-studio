protocols rsvp refresh-reduction
--------------------------------

**Minimum user role:** operator

In RSVP, states are maintained through the generation of RSVP refresh messages. These messages have two usages:

- To synchronize the state between RSVP neighbors

- To recover from lost RSVP messages

The following problems arise from relying on periodic refresh messages:

- Scalability - the periodic transmission and processing overhead of refresh messages for every RSVP session presents a scaling problem that increases as the number of sessions increases.

- Reliability and latency - the time to recover from the loss of RSVP messages is dependent on the refresh interval. A long refresh interval improves the transmission overhead, but at the cost of latency in state synchronization. A short refresh interval improves state synchronization (reliability), but at the cost of increased refresh message rate.

The RSVP refresh reduction option has the following capabilities that address these problems:

- RSVP message bundling - See "rsvp refresh-reduction aggregate".

- RSVP message ID - reduces message processing overhead - See "rsvp refresh-reduction reliable".

- Summary refresh - reduces the amount of information transmitted every refresh interval - enable both refresh-reduction aggregate and refresh-reduction reliable.

You can selectively enable or disable these capabilities on the Network Cloud. The RSVP full tunnel scale can only be reached if refresh-reduction is enabled.
The maximum MTU for a summary message and for an ACK message is the interface's L3 MTU.
Ack hold-time is 1 second.

To configure refresh-reduction:

1.	Enter RSVP refresh-reduction configuration mode:

2.	Proceed to configure the refresh-reduction options: "rsvp refresh-reduction aggregate" and "rsvp refresh-reduction reliable".

**Command syntax: refresh-reduction**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. - RSVP full tunnel scale can only be reached if refresh-reduction is enabled

.. - no command returns refresh-reduction settings to their default value

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# refresh-reduction
    dnRouter(cfg-protocols-rsvp-rr)#


**Removing Configuration**

To revert the refresh-reduction settings to their default value:
::

    dnRouter(cfg-protocols-rsvp)# no refresh-reduction

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
