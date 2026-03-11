protocols lldp tlv-filter
-------------------------

**Minimum user role:** operator

This command allows LLDP to disable non-mandatory TLV messages so that sensitive information about a network is not disclosed. To filter optional LLDP TLVs to be sent to peers:

**Command syntax: tlv-filter [optional-TLV-name]** [, optional-TLV-name, optional-TLV-name]

**Command mode:** config

**Hierarchies**

- protocols lldp

**Note**

- Multiple TLVs can be specified at once (separated by commas).

**Parameter table**

+-------------------+------------------------------------------------+-------------------------+---------+
| Parameter         | Description                                    | Range                   | Default |
+===================+================================================+=========================+=========+
| optional-TLV-name | Filter optional LLDP TLVs to be sent to peers. | | management-address    | \-      |
|                   |                                                | | port-description      |         |
|                   |                                                | | system-capabilities   |         |
|                   |                                                | | system-description    |         |
|                   |                                                | | system-name           |         |
+-------------------+------------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# tlv-filter management-address

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# tlv-filter management-address, system-capabilities


**Removing Configuration**

To remove specific optional TLVs from the LLDP TLV filter:
::

    dnRouter(cfg-protocols-lldp)# no tlv-filter management-address

::

    dnRouter(cfg-protocols-lldp)# no tlv-filter management-address, system-description

To remove the entire LLDP TLV filter:
::

    dnRouter(cfg-protocols-lldp)# no tlv-filter

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
