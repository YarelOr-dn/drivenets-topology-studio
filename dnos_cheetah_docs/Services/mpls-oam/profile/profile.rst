services mpls-oam profile
-------------------------

**Minimum user role:** operator


An MPLS-OAM profile serves for sending periodic LSP-ping packets as part of a test probe to verify RSVP tunnel functionality. Only one profile may be associated with an LSP. 

To configure a profile, enter profile configuration mode:

**Command syntax: profile [profile]**

**Command mode:** config

**Hierarchies**

- services mpls-oam

**Note**

- Profiles support MPLS-LSP ping only. To run a traceroute, use the "run traceroute mpls rsvp" and "run traceroute mpls bgp-lu" commands.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                      | Range            | Default |
+===========+==================================================================================+==================+=========+
| profile   | The profile name of the mpls oam service - the profile is atteched for an mpls   | | string         | \-      |
|           | protocol (e.g RSVP)                                                              | | length 1-255   |         |
+-----------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)#


**Removing Configuration**

To delete a certain profile:
::

    dnRouter(cfg-srv-mpls-oam)# # no profile P_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
