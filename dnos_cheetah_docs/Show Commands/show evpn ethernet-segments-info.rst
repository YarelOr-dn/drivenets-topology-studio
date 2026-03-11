show evpn ethernet-segments-info
--------------------------------

**Minimum user role:** operator

To show information relating to the ethernet-segments of EVPN instance(s).

**Command syntax: show evpn-vpws ethernet-segments-info** instance [evpn-name] esi [esi-value]

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-----------------------------------------+---------------+
| Parameter          | Description                             | Values                                  | Default value |
+====================+=========================================+=========================================+===============+
| evpn-name          | The name of the EVPN instance           | String                       | all      | \-            |
+--------------------+-----------------------------------------+-----------------------------------------+---------------+
| esi-value          | The esi 10 byte value                   | String - 10 hex octets separated by ':' | \-            |
+--------------------+-----------------------------------------+-----------------------------------------+---------------+

**Note:**

- Specifying an evpn-name will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the ethernet-segment information for all the EVPN instances.

- If the esi is specified then the ethernet-segment information for the specific esi will be shown.

**Example**
::

  dnRouter# show show evpn ethernet-segments-info

  EVPN: esi-scale_1
    EVI ID : 1
      Number of ESs: 1

       ESI                           | Nexthops             | Aliasing Label | Mode          | Role      
       --------------------------------------------------------------------------------------------------
       00:12:01:11:94:00:00:00:00:01 | 54.54.54.54          | 118671         | single-active | BDF       

  EVPN: evpn1
    EVI ID : 2
      Number of ESs: 1

       ESI                           | Nexthops             | Aliasing Label | Mode          | Role      
       --------------------------------------------------------------------------------------------------
       00:12:01:11:94:00:00:00:00:01 | 54.54.54.54          | 118671         | single-active | BDF        

  EVPN: evpn2
    EVI ID : 3
      Number of ESs: 1

      ESI                           | Nexthops             | Aliasing Label | Mode          | Role     
      --------------------------------------------------------------------------------------------------
      00:12:01:11:94:00:00:00:00:01 | ge400-0/0/10.1002    | 118673         | single-active | DF       
                                    | 54.54.54.54          | 118672         | single-active | BDF      


  show evpn ethernet-segments-info instance evpn1 esi 00:12:01:11:94:00:00:00:00:01

  EVPN: evpn1
    EVI ID : 2
      Number of ESs: 1

      ESI                           | Nexthops             | Aliasing Label | Mode          | Role
      --------------------------------------------------------------------------------------------------
      00:12:01:11:94:00:00:00:00:01 | ge400-0/0/10.1001    | 118672         | single-active | DF
                                    | 54.54.54.54          | 118671         | single-active | BDF
          

.. **Help line:** show detailed information for EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+