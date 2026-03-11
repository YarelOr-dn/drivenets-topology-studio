system snmp community
---------------------

**Minimum user role:** operator

An SNMP community is the grouping of an SNMP server with its authorized SNMP clients. You can define the relationship that the device has with the SNMP server by configuring SNMP community properties.

To configure community properties:

**Command syntax: community [community] vrf [vrf-name]** parameter [parameter-value]

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- SNMP community is a v1/v2c concept and is not related to v3.

- Notice the change in prompt from dnRouter(cfg-system-snmp)# to dnRouter(cfg-system-snmp-community)# (SNMP community configuration mode).

- User can configure multiple snmp communities per VRF

Validations :
    - Only 2 in-band VRFs and up to 1 out-of-band VRF are allowed to be in admin-state enabled:
        - VRF default
        - Single non-default VRF
        - VRF mgmt0
    - In case snmp community is configured with non-default VRF and a user is trying to delete the non-default VRF, the commit will fail on validation.
    - Up to 10 snmp servers are allowed to be configured in total.

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------+----------------------------+---------+
| Parameter | Description                                                                                                           | Range                      | Default |
+===========+=======================================================================================================================+============================+=========+
| community | The name for the SNMP community                                                                                       | string                     | \-      |
+-----------+-----------------------------------------------------------------------------------------------------------------------+----------------------------+---------+
| vrf-name  | Defines whether the client-list attachment to the snmp-server is via in-band (default VRF, or out-of-band (mgmt0 VRF) | default - in-band          | \-      |
|           |                                                                                                                       | non-default-vrf - in-band  |         |
|           |                                                                                                                       | mgmt0- out-of-band         |         |
+-----------+-----------------------------------------------------------------------------------------------------------------------+----------------------------+---------+

The following are the parameters that you can set for each community:

- system snmp community view

- system snmp community access

- system snmp community client-list

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
    dnRouter(cfg-system-snmp-community)# view MySnmpView
    dnRouter(cfg-system-snmp-community)# access read-only
    dnRouter(cfg-system-snmp-community)# clients 192.168.0.0/24
    dnRouter(cfg-system-snmp-community)# clients 172.17.0.0/16
    dnRouter(cfg-system-snmp-community)# clients 2001:db8:2222::/48
    dnRouter(cfg-system-snmp-community)# access read-write

    dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf my_vrf
    dnRouter(cfg-system-snmp-community)# view MySnmpView1
    dnRouter(cfg-system-snmp-community)# access read-only
    dnRouter(cfg-system-snmp-community)# clients 192.168.1.0/24
    dnRouter(cfg-system-snmp-community)# clients 172.17.1.0/16
    dnRouter(cfg-system-snmp-community)# clients 2001:db8:3333::/48


**Removing Configuration**

To remove the SNMP community configuration:
::

	dnRouter(cfg-system-snmp)# no community MySnmpCommunity vrf default


.. **Help line:** Configure system snmp server

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1.0   | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | no system snmp community command reverts to default configuration. |
|         | Applied new hierarchy for SNMP                                     |
+---------+--------------------------------------------------------------------+
| 9.0     | Applied new hierarchy for community                                |
+---------+--------------------------------------------------------------------+
| 13.1    | Added support for out-of-band community                            |
+---------+--------------------------------------------------------------------+
