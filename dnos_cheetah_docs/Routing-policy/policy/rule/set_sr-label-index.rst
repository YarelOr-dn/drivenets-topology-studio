routing-policy policy rule set sr-label-index
---------------------------------------------

**Minimum user role:** operator

Add Prefix-SID attribute to the matched prefix.
Prefix-SID attribute will include the Label-Index TLV with index value as set by user
Prefix-SID attribute will only be sent for IPv4/IPv6 Labeled Unicast prefixes
For a given prefix, if Prefix-SID attribute & Label-Index TLV exist and prefix-sid feature is enabled, bgp will allocate local label from Segment-Routing Global Block per required index

Set global-block-origination to add the Originator SRGB TLV (with value equal to local SRGB) for the Prefix-SID attribute resulted in label-index addition/modification

**Command syntax: set sr-label-index [sr-label-index]** global-block-origination

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter                | Description                                                                      | Range     | Default |
+==========================+==================================================================================+===========+=========+
| sr-label-index           | Add Prefix-SID attribute to the matched prefix. Prefix-SID attribute will        | 0-1048575 | \-      |
|                          | include the Label-Index TLV with index value as set by user                      |           |         |
+--------------------------+----------------------------------------------------------------------------------+-----------+---------+
| global-block-origination | Once enabled, when DNOS adds or update a prefix Prefix-SID attribute, add the    | \-        | \-      |
|                          | Originator SRGB TLV with DNOS local SRGB definition (RFC 8669 TLV 3 of           |           |         |
|                          | Prefix-SID attribute)                                                            |           |         |
+--------------------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set sr-label-index 10

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set sr-label-index 10 global-block-origination


**Removing Configuration**

To remove set protocols criteria:
::

    dnRouter(cfg-rpl-policy-rule-10)# no set sr-label-index

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
