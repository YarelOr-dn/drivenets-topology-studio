protocols rsvp interface protection bypass-tunnel
-------------------------------------------------

**Minimum user role:** operator

Bypass tunnels can be created manually or automatically. If there is a link failure for the interface, the bypass tunnel can us as an alternate path for the affected LSP passing through the failed interface.
You can assign up to 32 manual bypass tunnels per interface. Only tunnels configured with the "bypass" flag can serve as bypass tunnels. A bypass tunnel can be assigned to one RSVP interface only.
To assign a manual bypass tunnel to protects the interface against link failure:

**Command syntax: bypass-tunnel [bypass-tunnel]** [, bypass-tunnel, bypass-tunnel]

**Command mode:** config

**Hierarchies**

- protocols rsvp interface protection

**Note**
- Removing a manual bypass tunnel from an interface will result in closing the bypass tunnel, even if it is currently carrying traffic.

..
	-  a bypass-tunnel can be assigned to one rsvp interface only

	-  removing a manual-bypass-tunnel from an interface will result in closing the bypass-tunnel, even if it currently carries traffic.

	-  'no bypass-tunnel [tunnel-name]' - remove the specified manual-bypass-tunnels

	-  'no bypass-tunnel' - remove all manual-bypass-tunnels that protect the interface

**Parameter table**

+---------------+----------------------------------------+------------------+---------+
| Parameter     | Description                            | Range            | Default |
+===============+========================================+==================+=========+
| bypass-tunnel | manual tunnel protecting the interface | | string         | \-      |
|               |                                        | | length 1-255   |         |
+---------------+----------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-1
    dnRouter(cfg-protocols-rsvp-if)# protection
    dnRouter(cfg-rsvp-if-protection)# bypass-tunnel BACKUP_1
    dnRouter(cfg-rsvp-if-protection)# bypass-tunnel BACKUP_7


    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-2
    dnRouter(cfg-protocols-rsvp-if)# protection
    dnRouter(cfg-rsvp-if-protection)# bypass-tunnel BACKUP_2,BACKUP_3,BACKUP_4,BACKUP_5,BACKUP_6


**Removing Configuration**

To remove a specific manual bypass-tunnel:
::

    dnRouter(cfg-rsvp-if-protection)# no bypass-tunnel BACKUP_2,BACKUP_3

To remove all manual bypass-tunnels from protecting the interface:
::

    dnRouter(cfg-rsvp-if-protection)# no bypass-tunnel

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
