protocols pim address-family mofrr umh-selection-mode
-----------------------------------------------------

**Minimum user role:** operator

Upstream multicast hop (UMH) selection-mode operates in either ECMP mode or non-ECMP mode:

In ECMP-mode, the selected standby-UMH will only be an ECMP path to the primary if exists.
In Non-ECMP mode, the standby-UMH will preferably be an uplink node-disjoint LFA alternative (in order to minimize the chance that an upstream node failure will impact the MoFRR success). In case there is no node disjoint LFA, the fallback is link disjoint LFA path, and the last fallback is ECMP in the event that niether node nor link disjoint LFA exist.

To configure MoFRR UMH selection mode:

**Command syntax: umh-selection-mode [umh-selection-mode]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family mofrr

**Parameter table**

+--------------------+--------------------------------+--------------+----------+
| Parameter          | Description                    | Range        | Default  |
+====================+================================+==============+==========+
| umh-selection-mode | The type of UMH selection-mode | | ecmp       | non-ecmp |
|                    |                                | | non-ecmp   |          |
+--------------------+--------------------------------+--------------+----------+

**Example**
::

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-address-family)# mofrr
    dnRouter(cfg-pim-address-family-mofrr)# umh-selection-mode ecmp

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-address-family)# mofrr
    dnRouter(cfg-pim-address-family-mofrr)# umh-selection-mode non-ecmp


**Removing Configuration**

To revert the UMH selection mode configuration to default:
::

    dnRouter(cfg-pim-address-family-mofrr)# no umh-selection-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
