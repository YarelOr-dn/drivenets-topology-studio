# TEST_mac_mob_scale_64k_G3

**Device:** PE-1
**Mode:** dry-run
**Time:** 2026-04-20T07:47:35+00:00

```json
{
  "prerequisites": {
    "test_id": "TEST_mac_mob_scale_64k_G3",
    "device": "PE-1",
    "rows": [
      {
        "check": "evpn_instance",
        "status": "PASS",
        "detail": "HA_TEST_ELAN present (live)",
        "fix_via": "config_generator.build_minimal_si_evpn_snippet + validate_config",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "bgp_l2vpn_evpn",
        "status": "FAIL",
        "detail": "0/3 Established (live)",
        "fix_via": "Manual BGP L2VPN EVPN peering or scaler wizard",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "seamless_integration",
        "status": "PASS",
        "detail": "seamless-integration present (live)",
        "fix_via": "Add seamless-integration under EVPN instance (no IRB allowed)",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "mac_table_populated",
        "status": "FAIL",
        "detail": "count=0 (live)",
        "fix_via": "/SPIRENT l2 -- create L2 devices to learn MACs",
        "auto_fixable": true,
        "spirent_action": "spirent_create_l2_devices"
      },
      {
        "check": "two_acs",
        "status": "PASS",
        "detail": "AC interfaces (live): 8",
        "fix_via": "Add second AC on bridge-domain / /SPIRENT dnaas fix for second VLAN path",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "pseudowire",
        "status": "PASS",
        "detail": "False",
        "fix_via": "Configure VPLS pseudowire attachment",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "multihoming_esi",
        "status": "PASS",
        "detail": "False",
        "fix_via": "Configure ethernet-segment / multihoming",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "cluster_for_ha",
        "status": "PASS",
        "detail": "standalone",
        "fix_via": "NCC cluster with standby required for switchover tests",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "spirent_available",
        "status": "PASS",
        "detail": "spirent_tool.py found",
        "fix_via": "Install spirent_tool.py or set SPIRENT_HOME",
        "auto_fixable": false,
        "spirent_action": null
      },
      {
        "check": "dnaas_path",
        "status": "WARN",
        "detail": "No bridge-domain detected (live)",
        "fix_via": "/SPIRENT dnaas fix",
        "auto_fixable": true,
        "spirent_action": "spirent_dnaas_check"
      },
      {
        "check": "config:bgp_l2vpn_evpn_af",
        "status": "FAIL",
        "detail": "Config block not found: BGP L2VPN EVPN address-family (required for EVPN peering)",
        "fix_via": "Config snippet available (49 chars)",
        "auto_fixable": false,
        "spirent_action": null,
        "fix_snippet": "protocols bgp 65000\n  address-family l2vpn-evpn\n!"
      }
    ],
    "overall": "FAIL",
    "config_delta": {
      "proposals": [
        {
          "id": "bgp_peering",
          "description": "Establish BGP L2VPN EVPN neighbors (manual / lab).",
          "risk": "high"
        },
        {
          "id": "pseudowire",
          "description": "Add VPLS PW for PW-related scenarios (SW-205162/198/199).",
          "risk": "high"
        }
      ],
      "irb_forbidden_with_si": true
    },
    "config_gaps": {
      "evpn_name": "HA_TEST_ELAN",
      "test_id": "TEST_mac_mob_scale_64k_G3",
      "gaps": [
        {
          "requirement_id": "bgp_l2vpn_evpn_af",
          "requirement": {
            "path": "protocols bgp {asn} address-family l2vpn-evpn",
            "description": "BGP L2VPN EVPN address-family (required for EVPN peering)",
            "required_for": [
              "all"
            ],
            "detect_keyword": "l2vpn-evpn",
            "example_value": "",
            "auto_fixable": false
          },
          "status": "missing",
          "detail": "Config block not found: BGP L2VPN EVPN address-family (required for EVPN peering)",
          "fix_snippet": ""
        }
      ],
      "snippets": {
        "bgp_l2vpn_evpn_af": "protocols bgp 65000\n  address-family l2vpn-evpn\n!"
      },
      "gap_count": 1,
      "all_present": false,
      "auto_fixable_count": 0
    },
    "auto_fixable_items": [
      "mac_table_populated",
      "dnaas_path"
    ]
  },
  "runtime_params": {
    "active_ncc_id": "0",
    "evpn_name": "HA_TEST_ELAN",
    "test_mac": "00:DE:AD:00:01:01",
    "ncp_id": "0",
    "_ac_outer_vlan_map": "{\"1\": 214, \"2\": 214, \"3\": 214, \"4\": 214, \"5\": 214, \"6\": 103, \"7\": 103, \"8\": 103, \"9\": 103, \"10\": 103, \"11\": 103, \"15\": 102, \"16\": 103, \"17\": 103, \"18\": 103, \"19\": 103, \"20\": 103, \"21\": 103, \"22\": 103, \"23\": 103, \"24\": 103, \"25\": 103, \"26\": 103, \"27\": 103, \"28\": 103, \"29\": 103, \"30\": 103, \"31\": 103, \"32\": 103, \"33\": 103, \"34\": 103, \"35\": 103, \"36\": 103, \"37\": 103, \"38\": 103, \"39\": 103, \"40\": 103, \"41\": 103, \"42\": 103, \"43\": 103, \"44\": 103, \"45\": 103, \"46\": 103, \"47\": 103, \"48\": 103, \"49\": 103, \"50\": 103, \"51\": 103, \"52\": 103, \"53\": 103, \"54\": 103, \"55\": 103, \"56\": 103, \"57\": 103, \"58\": 103, \"59\": 103, \"60\": 103, \"61\": 103, \"62\": 103, \"63\": 103, \"64\": 103, \"65\": 103, \"66\": 103, \"67\": 103, \"68\": 103, \"69\": 103, \"70\": 103, \"71\": 103, \"72\": 103, \"73\": 103, \"74\": 103, \"75\": 103, \"76\": 103, \"77\": 103, \"78\": 103, \"79\": 103, \"80\": 103, \"81\": 103, \"82\": 103, \"83\": 103, \"84\": 103, \"85\": 103, \"86\": 103, \"87\": 103, \"88\": 103, \"89\": 103, \"90\": 103, \"91\": 103, \"92\": 103, \"93\": 103, \"94\": 103, \"95\": 103, \"96\": 103, \"97\": 103, \"98\": 103, \"99\": 103, \"103\": 103, \"104\": 103, \"105\": 103, \"106\": 103, \"107\": 103, \"108\": 103, \"109\": 103, \"110\": 103, \"111\": 103, \"112\": 103, \"113\": 103, \"114\": 103, \"115\": 103, \"116\": 103, \"117\": 103, \"118\": 103, \"119\": 103, \"120\": 103, \"121\": 103, \"122\": 103, \"123\": 103, \"124\": 103, \"125\": 103, \"126\": 103, \"127\": 103, \"128\": 103, \"129\": 103, \"130\": 103, \"131\": 103, \"132\": 103, \"133\": 103, \"134\": 103, \"135\": 103, \"136\": 103, \"137\": 103, \"138\": 103, \"139\": 103, \"140\": 103, \"141\": 103, \"142\": 103, \"143\": 103, \"144\": 103, \"145\": 103, \"146\": 103, \"147\": 103, \"148\": 103, \"149\": 103, \"150\": 103, \"151\": 103, \"152\": 103, \"153\": 103, \"154\": 103, \"155\": 103, \"156\": 103, \"157\": 103, \"158\": 103, \"159\": 103, \"160\": 103, \"161\": 103, \"162\": 103, \"163\": 103, \"164\": 103, \"165\": 103, \"166\": 103, \"167\": 103, \"168\": 103, \"169\": 103, \"170\": 103, \"171\": 103, \"172\": 103, \"173\": 103, \"174\": 103, \"175\": 103, \"176\": 103, \"177\": 103, \"178\": 103, \"179\": 103, \"180\": 103, \"181\": 103, \"182\": 103, \"183\": 103, \"184\": 103, \"185\": 103, \"186\": 103, \"187\": 103, \"188\": 103, \"189\": 103, \"190\": 103, \"191\": 103, \"192\": 103, \"193\": 103, \"194\": 103, \"195\": 103, \"196\": 103, \"197\": 103, \"198\": 103, \"199\": 103, \"200\": 103, \"201\": 103, \"202\": 103, \"203\": 103, \"204\": 103, \"205\": 103, \"206\": 103, \"207\": 103, \"208\": 103, \"209\": 103, \"210\": 103, \"211\": 103, \"212\": 103, \"213\": 103, \"214\": 103, \"215\": 103, \"216\": 103, \"217\": 103, \"218\": 103, \"219\": 103, \"220\": 103, \"221\": 103, \"222\": 103, \"223\": 103, \"224\": 103, \"225\": 103, \"226\": 103, \"227\": 103, \"228\": 103, \"229\": 103, \"230\": 103, \"231\": 103, \"232\": 103, \"233\": 103, \"234\": 103, \"235\": 103, \"236\": 103, \"237\": 103, \"238\": 103, \"239\": 103, \"240\": 103, \"241\": 103, \"242\": 103, \"243\": 103, \"244\": 103, \"245\": 103, \"246\": 103, \"247\": 103, \"248\": 103, \"249\": 103, \"250\": 103, \"251\": 103, \"252\": 103, \"253\": 103, \"254\": 103, \"255\": 103, \"256\": 103, \"257\": 103, \"258\": 103, \"259\": 103, \"260\": 103, \"261\": 103, \"262\": 103, \"263\": 103, \"264\": 103, \"265\": 103, \"266\": 103, \"267\": 103, \"268\": 103, \"269\": 103, \"270\": 103, \"271\": 103, \"272\": 103, \"273\": 103, \"274\": 103, \"275\": 103, \"276\": 103, \"277\": 103, \"278\": 103, \"279\": 103, \"280\": 103, \"281\": 103, \"282\": 103, \"283\": 103, \"284\": 103, \"285\": 103, \"286\": 103, \"287\": 103, \"288\": 103, \"289\": 103, \"290\": 103, \"291\": 103, \"292\": 103, \"293\": 103, \"294\": 103, \"295\": 103, \"296\": 103, \"297\": 103, \"298\": 103, \"299\": 103, \"300\": 103, \"301\": 103, \"302\": 103, \"303\": 103, \"304\": 103, \"305\": 103, \"306\": 103, \"1000\": 214, \"1001\": 214, \"1002\": 214, \"1010\": 214, \"1011\": 214, \"2000\": 210, \"2001\": 210}",
    "_si_ac1_inner_vlan": "1000",
    "_si_ac2_inner_vlan": "1001",
    "_si_outer_vlan": "214",
    "_evpn_ac_interfaces": "ge400-0/0/4.1000,ge400-0/0/5.1000,ge400-0/0/5.1001,ge400-0/0/5.1002,ge400-0/0/5.2000,ge400-0/0/5.2001,ge400-0/0/12.1000",
    "_evpn_ac1_interface": "ge400-0/0/4.1000",
    "_evpn_si_site_interface": "ge400-0/0/5.1000",
    "asn": "1234567",
    "pw_test_evpn_name": "PW_TEST_ELAN",
    "pw_vlan": "1010",
    "pw_evpn_name": "PW_TEST_ELAN",
    "_pw_ac1_interface": "ge400-0/0/5.1010",
    "_pw_ac_interfaces": "ge400-0/0/5.1010,ge400-0/0/5.1011",
    "_pw_ac_interface": "ge400-0/0/5.1010",
    "pw_outer_vlan": "214",
    "pw_inner_vlan": "1010",
    "pw_dut_mac": "e8:c5:7a:39:b6:6a",
    "rd": "1.1.1.1:500",
    "rt": "100:100",
    "rt_import": "100:100",
    "rt_export": "100:100",
    "evi": "1",
    "pw_rt": "9990:9990",
    "pw_rd": "1.1.1.1:9990",
    "pw_evi": "6",
    "spirent_evpn_device": "EVPN_RT2_Peer",
    "spirent_bgp_device": "EVPN_RT2_Peer",
    "spirent_evpn_next_hop": "17.17.17.2",
    "_si_dut_mac": "e8:c5:7a:d8:96:20"
  },
  "dry_plan": {
    "id": "TEST_mac_mob_scale_64k_G3",
    "scenarios": [
      {
        "id": "SC01_bulk_learn_64k",
        "expanded_commands": [
          {
            "phase": "snapshot",
            "cmd": "show evpn mac summary | no-more"
          },
          {
            "phase": "snapshot",
            "cmd": "show system npu-resources ncp 0 | no-more"
          },
          {
            "phase": "verify",
            "cmd": "show evpn mac summary | no-more"
          },
          {
            "phase": "verify",
            "cmd": "show system npu-resources ncp 0 | no-more"
          }
        ],
        "trigger_plan": {
          "scenario_id": "SC01_bulk_learn_64k",
          "from": "spirent_send_64k_macs_ac1",
          "to": "spirent_bulk_learn_assert",
          "primary_method": "spirent",
          "available_methods": [
            "spirent",
            "manual"
          ],
          "operator_steps": [
            {
              "action": "ensure_learned",
              "detail": "Verify 1 MAC(s) learned on spirent_send_64k_macs_ac1"
            },
            {
              "action": "shift_traffic",
              "detail": "Move traffic so same MAC(s) appear on spirent_bulk_learn_assert"
            },
            {
              "action": "verify_move",
              "detail": "show evpn mac-table instance {evpn_name} mac {test_mac} | no-more"
            }
          ],
          "spirent_strategy": "Create L2 device blocks with same MAC pool on VLANs mapped to spirent_send_64k_macs_ac1 and spirent_bulk_learn_assert. Start traffic on spirent_send_64k_macs_ac1 VLAN to learn, stop, start on spirent_bulk_learn_assert VLAN to trigger move.",
          "scale_note": "For 64K MACs: spirent_tool.py create-device --device-count 65536 --mac-step 1. One REST call via STC Device Block multiplier (~5s)."
        }
      },
      {
        "id": "SC02_bulk_move_64k_ac1_to_ac2",
        "expanded_commands": [
          {
            "phase": "snapshot",
            "cmd": "show evpn mac summary | no-more"
          },
          {
            "phase": "snapshot",
            "cmd": "show evpn mac-table instance HA_TEST_ELAN | count"
          },
          {
            "phase": "poll_convergence",
            "cmd": "show evpn mac summary | no-more"
          },
          {
            "phase": "poll_convergence",
            "cmd": "show evpn forwarding-table mac-address-table instance HA_TEST_ELAN | count"
          },
          {
            "phase": "verify",
            "cmd": "show evpn mac summary | no-more"
          },
          {
            "phase": "verify",
            "cmd": "show dnos-internal routing evpn mac-mobility-redis-count | no-more"
          },
          {
            "phase": "verify",
            "cmd": "show system npu-resources ncp 0 | no-more"
          }
        ],
        "trigger_plan": {
          "scenario_id": "SC02_bulk_move_64k_ac1_to_ac2",
          "from": "spirent_move_64k_ac1_to_ac2",
          "to": "spirent_bulk_learn_assert",
          "primary_method": "spirent",
          "available_methods": [
            "spirent",
            "manual"
          ],
          "operator_steps": [
            {
              "action": "ensure_learned",
              "detail": "Verify 1 MAC(s) learned on spirent_move_64k_ac1_to_ac2"
            },
            {
              "action": "shift_traffic",
              "detail": "Move traffic so same MAC(s) appear on spirent_bulk_learn_assert"
            },
            {
              "action": "verify_move",
              "detail": "show evpn mac-table instance {evpn_name} mac {test_mac} | no-more"
            }
          ],
          "spirent_strategy": "Create L2 device blocks with same MAC pool on VLANs mapped to spirent_move_64k_ac1_to_ac2 and spirent_bulk_learn_assert. Start traffic on spirent_move_64k_ac1_to_ac2 VLAN to learn, stop, start on spirent_bulk_learn_assert VLAN to trigger move.",
          "scale_note": "For 64K MACs: spirent_tool.py create-device --device-count 65536 --mac-step 1. One REST call via STC Device Block multiplier (~5s)."
        }
      },
      {
        "id": "SC03_suppression_at_scale",
        "expanded_commands": [
          {
            "phase": "verify",
            "cmd": "show evpn mac-table instance HA_TEST_ELAN suppress | no-more"
          },
          {
            "phase": "verify",
            "cmd": "show evpn mac summary | no-more"
          },
          {
            "phase": "verify",
            "cmd": "show bgp l2vpn evpn summary | no-more"
          }
        ],
        "trigger_plan": {
          "scenario_id": "SC03_suppression_at_scale",
          "from": "rapid_64k_flap_3_times",
          "to": "spirent_bulk_learn_assert",
          "primary_method": "spirent",
          "available_methods": [
            "spirent",
            "manual"
          ],
          "operator_steps": [
            {
              "action": "ensure_learned",
              "detail": "Verify 1 MAC(s) learned on rapid_64k_flap_3_times"
            },
            {
              "action": "shift_traffic",
              "detail": "Move traffic so same MAC(s) appear on spirent_bulk_learn_assert"
            },
            {
              "action": "verify_move",
              "detail": "show evpn mac-table instance {evpn_name} mac {test_mac} | no-more"
            }
          ],
          "spirent_strategy": "Create L2 device blocks with same MAC pool on VLANs mapped to rapid_64k_flap_3_times and spirent_bulk_learn_assert. Start traffic on rapid_64k_flap_3_times VLAN to learn, stop, start on spirent_bulk_learn_assert VLAN to trigger move.",
          "scale_note": "For 64K MACs: spirent_tool.py create-device --device-count 65536 --mac-step 1. One REST call via STC Device Block multiplier (~5s)."
        }
      }
    ]
  },
  "command_validation": [
    {
      "original": "show dnos-internal routing evpn mac-mobility-redis-count | no-more",
      "corrected": "show evpn mac-table summary | no-more"
    }
  ],
  "live_validation": [
    {
      "prereq_id": "bgp_evpn",
      "command": "show bgp l2vpn evpn summary | no-more",
      "was_unvalidated": "False",
      "status": "VALID",
      "output_preview": "BGP router identifier 1.1.1.1, local AS number 1234567\nBGP table node count 2\n\n  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted\n  2.2.2.2         4 "
    },
    {
      "prereq_id": "evpn_instance",
      "command": "show evpn summary | no-more",
      "was_unvalidated": "False",
      "status": "VALID",
      "output_preview": "Global EVPN parameters\nMAC table limit per EVI : 64000\nMAC table aging time    : 320s\nControl Word            : enabled\nFAT Label               : disabled\nE-Tree Leaf Label       : 1032383\n\nNumber of "
    },
    {
      "prereq_id": "spirent",
      "command": "manual: /SPIRENT status",
      "status": "SKIPPED",
      "note": "Not a device show command or has unresolved params"
    },
    {
      "prereq_id": "two_ac",
      "command": "show config network-services evpn instance HA_TEST_ELAN | no-more",
      "was_unvalidated": "False",
      "status": "VALID",
      "output_preview": "# YOR_PE-1 config-start [20-Apr-2026 10:47:35 UTC+03:00 (Israel)]\n\nnetwork-services\n  evpn\n    instance HA_TEST_ELAN\n      protocols\n        bgp 1234567\n          export-l2vpn-evpn route-target 100:10"
    },
    {
      "prereq_id": "suppression_cfg",
      "command": "show config network-services evpn instance HA_TEST_ELAN mac-handling | no-more",
      "was_unvalidated": "False",
      "status": "VALID",
      "output_preview": "# YOR_PE-1 config-start [20-Apr-2026 10:47:35 UTC+03:00 (Israel)]\n\nnetwork-services\n  evpn\n    instance HA_TEST_ELAN\n      mac-handling\n        loop-prevention\n          admin-state enabled\n          "
    }
  ]
}
```