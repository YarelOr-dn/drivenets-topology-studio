show ospf traffic-engineering database
--------------------------------------

**Minimum user role:** viewer

DIsplays the OSPF traffic-engineering topology for the specified router-id, if the router-id is not specified in the TE topology for all the area routers.



**Command syntax: show ospf traffic-engineering database** [router-id]

**Command mode:** operational



**Note**

- The following information is displayed per router-id:

  - OSPF Router ID / OSPF TE ID / OSPF area

  - Per TE link:

  - link network type / Neighbour Router ID

  - Neighbour Interface Address

  - Link TE metric, Link IGP metric

  - Admin group

  - SRLG values

  - DiffServ model: {RDM}

  - Physical BW, Max Reservable BW

  - BW pools.

.. - router-id  is optional

  **Displays the following information per router-id:**

  - OSPF Router ID / OSPF TE ID / OSPF area
  - And the following per TE link information:
    - link network type / Neighbour Router ID
    - Interface IP address
    - Neighbour Interface Address
    - Link TE metric, Link IGP metric
    - Admin group
    - SRLG values
    - DiffServ model: {RDM}
    - Physical BW, Max Reservable BW
    - BW pools

**Parameter table**

+-----------+-------------------------------+-----------------------------------------+---------------+
| Parameter | Description                   | Range                                   | Default value |
+===========+===============================+=========================================+===============+
| router-id | The ID of the specific router | All Router-IDs in the related OSPF area | \-            |
+-----------+-------------------------------+-----------------------------------------+---------------+

**Example**
::

  dnRouter# show ospf traffic-engineering database 4.4.4.4

  IGP Id: 4.4.4.4, MPLS TE Id: 4.4.4.4 Router Node  (OSPF area 0)

    Link[0]:Point-to-Point, Nbr IGP Id:1.1.1.1
      Intf Address:10.1.14.4
      Nbr Intf Address:10.1.14.1
      TE Metric:10, IGP Metric:10
      Admin Group: 0x00000001
      BC Model ID:RDM
      Physical BW:1000000 (kbps), Max Reservable BW Global:10000 (kbps)
      Max Reservable BW Sub:0 (kbps)
      Unreserved BW (kbps):
        [0]: 10000        [1]: 10000
        [2]: 10000        [3]: 10000
        [4]: 10000        [5]: 10000
        [6]: 10000        [7]: 10000



  dnRouter# show ospf traffic-engineering database

  IGP Id: 1.1.1.1, MPLS TE Id: 1.1.1.1 Router Node  (OSPF 1 area 0)

    Link[0]:Point-to-Point, Nbr IGP Id:2.2.2.2
      Intf Address:10.1.12.1
      Nbr Intf Address:10.1.12.2
      TE Metric:3, IGP Metric:3
      Admin Group: 0x00000003
      Extended Admin Group: 0x00000003
      SRLGs: 123
      BC Model ID:RDM
      Physical BW:1000000 (kbps), Max Reservable BW Global:0 (kbps)
      Max Reservable BW Sub:0 (kbps)
      Unreserved BW (kbps):
        [0]:     0        [1]:     0
        [2]:     0        [3]:     0
        [4]:     0        [5]:     0
        [6]:     0        [7]:     0

    Link[1]:Point-to-Point, Nbr IGP Id:8.8.8.8
      Intf Address:10.1.18.1
      Nbr Intf Address:10.1.18.8
      TE Metric:10, IGP Metric:10
      SRLGs: 123
      Admin Group: 0x00000000
      Extended Admin Group: 0x00000000 0x00000100
      SRLGs: 234, 543
      BC Model ID:RDM
      Physical BW:1000000 (kbps), Max Reservable BW Global:10000 (kbps)
      Max Reservable BW Sub:0 (kbps)
      Unreserved BW (kbps):
        [0]: 10000        [1]: 10000
        [2]: 10000        [3]: 10000
        [4]: 10000        [5]: 10000
        [6]: 10000        [7]:  9250

    Link[2]:Point-to-Point, Nbr IGP Id:4.4.4.4
      Intf Address:10.1.14.1
      Nbr Intf Address:10.1.14.4
      TE Metric:10, IGP Metric:10
      Admin Group: 0x00000000
      Extended Admin Group: 0x00000000
      SRLGs: 123
      BC Model ID:RDM
      Physical BW:1000000 (kbps), Max Reservable BW Global:0 (kbps)
      Max Reservable BW Sub:0 (kbps)
      Unreserved BW (kbps):
        [0]:     0        [1]:     0
        [2]:     0        [3]:     0
        [4]:     0        [5]:     0
        [6]:     0        [7]:     0

.. **Help line:** Displays the OSPF TE Topology for the specified router-id.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 13.1    | Command introduced                  |
+---------+-------------------------------------+
| 19.1    | Extended Admin Groups support added |
+---------+-------------------------------------+
