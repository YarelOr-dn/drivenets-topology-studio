protocols isis instance address-family ipv4-unicast ti-fast-reroute srlg-asla
-----------------------------------------------------------------------------

**Minimum user role:** operator

When enabled, DNOS advertises the SRLG information under an application specific SRLG TLV (type 238) for the application type LFA (SABM with F bit).
When enabled, DNOS honors the received application specific SRLG TLVs.
When recevied with the application type LFA (SABM with F bit) any ti-fast-reroute calculation that is require to consider SRLG, utilizes the application specific TLV information regarding the SRLG link values.

To enable the LFA SRLG aplication specific Link Attribute:

**Command syntax: srlg-asla [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast ti-fast-reroute

**Note**
- The local SRLG is configured under 'protocols mpls traffic-engineering interface <if-name> srlg-group', and is applied for any SRLG advertisement type, i.e legacy and ASLA.
- Once enabled, the ASLA LFA SRLG will be advertised, regardless if the ASLA SR SRLG (S bit) or ASLA Flex-Algo SRLG (X bit) are advertised.
- The SRLG-ASLA configuration is per address-family (i.e topology). Enabling it in a given address-family results in:
-- Advertising the ASLA SRLG TLV 238 which may serve both address families in remote routers.
-- Locally, only the enabled address-family honores received the ASLA SRLG TLV 238 for this address-family (i.e topology) TI-LFA calculations.
- For a given address-family SRLG-ASLA, once enabled, if the ASLA SRLG TLV is not recevied, or received with an L-FLAG, or the F-bit is not set, DNOS leverages the legacy SRLG TLVs in the ti-lfa calculation.
- ASLA LFA SRLG is advertised without an L flag by default and include the configured SRLG values. In case the use-legacy-te is enabled, it sets the L-FLAG in SRLG TLV 238.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enable advertisement and reception of srlg information under Application         | | enabled    | disabled |
|             | Specific SRLG TLV (type 238) for application type LFA (SABM with F bit)          | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# srlg-asla enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# srlg-asla enabled


**Removing Configuration**

To revert the srlg-asla to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no srlg-asla

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
