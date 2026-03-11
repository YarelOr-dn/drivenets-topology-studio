interfaces fec
--------------

**Minimum user role:** operator

The Forward Error Correction (FEC) provides coding gain to increase the link budget and BER performance.

You can enable or disable Forward Error Correction (FEC) for a physical Ethernet interface, as follows:

-	Clause 74 of the IEEE 802.3 standard. For a PHY with a multi-lane BASE-R PCS, the FEC sublayer is instantiated for each PCS lane and operates autonomously on a per PCS lane basis.

	Encoding based on FC-FEC(2112,2080) ("fire-code") supporting the inter-sublayer interfaces:

	-	10GBASE-R PHY
	-	40GBASE-R PHY
	-	100GBASE-R PHY
-	Clause 91 of the IEEE 802.3 standard, which specifies a Reed-Solomon Forward Error Correction (RS-FEC) sublayer for 100GBASE-R PHYs.

	Encoding based on RS-FEC(528,514) supporting the inter-sublayer interfaces:

	-	100GBASE-CR4 PHY
	-	100GBASE-KR4 PHY
	-	100GBASE-SR4 PHY

	Encoding based on RS-FEC(544,514) supporting the inter-sublayer interfaces:

	-	100GBASE-KP4 PHY
-	Clause 119 of the IEEE P802.3bs

	Encoding based on RS-FEC(544,514) supporting the inter-sublayer interfaces:

	-	400GBASE-R PHY

To configure the interface FEC:

**Command syntax: fec [fec-type]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to physical interfaces.

**Parameter table**

+-----------+---------------------------------------------+--------------------+-----------------------------+
| Parameter | Description                                 | Range              | Default                     |
+===========+=============================================+====================+=============================+
| fec-type  | The type of FEC to enable for the interface | | none             | | None for 10G/100G         |
|           |                                             | | rs-fec-528-514   | | rs-fec-544-514 for 400G   |
|           |                                             | | rs-fec-544-514   |                             |
+-----------+---------------------------------------------+--------------------+-----------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-2/1/1
    dnRouter(cfg-if-ge100-2/1/1)# fec rs-fec-544-514
    dnRouter(cfg-if-ge100-2/1/1)# fec rs-fec-528-514
    dnRouter(cfg-if-ge100-2/1/1)# fec none


**Removing Configuration**

To revert to the default type:
::

    dnRouter(cfg-if-ge100-2/1/1)# no fec

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 10.0    | Command introduced   |
+---------+----------------------+
| 11.0    | Added rs-fec-544-514 |
+---------+----------------------+
