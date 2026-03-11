protocols isis instance flex-algo use-legacy-te
-----------------------------------------------

**Minimum user role:** operator

User will have the option of leveraging Legacy TLVs for distributing Traffic-Engineering information which will also serve SR Flex-algo, instead of dedicated Application-Specific Link Attributes (ASLA) TLVs (RFC 8919)
When enabled: If ASLA information is required to be advertise due to participation in one (or more) SR Flex-Algo,  L-flag (Legacy) will be set in SABM TLV and no dedicated sub-tlvs will be required for ASLA TE information. Information is carried in legacy ISIS TE tlvs
When disabled:  If ASLA information is required to be advertise due to participation in one (or more) SR Flex-Algo,  L-flag (Legacy) will not be set in SABM TLV. Any required TE information, such as admin-groups, extended-admin-groups, te-metric, srlg and link delay, will be advertise with dedicated ASLA sub-tlv.
To set usage of legacy te:

**Command syntax: use-legacy-te [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance flex-algo

**Note**

- Reconfiguring will trigger LSP update

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Set if Legacy tlvs should be used to advertise flex-algo application specific    | | enabled    | disabled |
|             | traffic-engineering tlvs                                                         | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-inst-sr-flex-algo)# use-legacy-te disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-inst-sr-flex-algo)# no use-legacy-te

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
