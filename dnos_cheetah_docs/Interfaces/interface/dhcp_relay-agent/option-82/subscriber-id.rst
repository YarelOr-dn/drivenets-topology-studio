interfaces dhcp relay-agent option-82 subscriber-id
---------------------------------------------------

**Minimum user role:** operator

To set the default DHCP Relay Agent Information Option (option 82) subscriber ID sub-option on the interface:

**Command syntax: subscriber-id [subscriber-id]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Note**

- User configured string may only contain alphanumeric characters, underscores, hyphens, dots, forward slashes, backslashes and colons.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+-----------------+---------+
| Parameter     | Description                                                                      | Range           | Default |
+===============+==================================================================================+=================+=========+
| subscriber-id | Allows DHCP relay agent to associate a stable Subscriber ID with DHCP client     | | string        | \-      |
|               | messages in a way that is independent of the client and of the underlying        | | length 1-63   |         |
|               | physyical network infrastructure                                                 |                 |         |
+---------------+----------------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# subscriber-id mySubscriberID


**Removing Configuration**

To renive DHCP relay agent information option subscriber ID sub-option configuration on the interface:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no subscriber-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
