/**
 * topology-sample-data.js - Sample Topology Data
 * 
 * Extracted from topology.js for modular architecture.
 * Contains sample DNAAS topology data for demos and testing.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.SampleTopologyData = {

    /**
     * LOGICAL VIEW: Sub-interface labels attached to link
     * Simple PE-to-PE L2 service topology
     */
    getDnaasLogicalBD210Topology() {
        return {
            "version": "1.0",
            "objects": [
                // ===== DEVICES =====
                { "id": "device_pe1", "type": "device", "deviceType": "router", "x": 200, "y": 350, "radius": 70, "rotation": 0, "color": "#3498db", "label": "YOR_PE-1", "locked": false, "visualStyle": "circle" },
                { "id": "device_pe2", "type": "device", "deviceType": "router", "x": 1100, "y": 350, "radius": 70, "rotation": 0, "color": "#3498db", "label": "YOR_PE-2", "locked": false, "visualStyle": "circle" },
                
                // ===== LINK - L2 Service =====
                { "id": "link_l2", "type": "link", "originType": "QL", "device1": "device_pe1", "device2": "device_pe2", "color": "#2ecc71",
                  "start": { "x": 270, "y": 350 }, "end": { "x": 1030, "y": 350 }, "style": "solid", "width": 6,
                  "linkDetails": {
                    "interfaceA": "ge400-0/0/4.210", "interfaceB": "bundle-100.210",
                    "ipTypeA": "L2-Service", "ipTypeB": "L2-Service"
                  }
                },
                
                // ===== TITLE =====
                { "id": "text_title", "type": "text", "x": 650, "y": 120, "text": "L2 Service (Logical View)", "fontSize": "28px", "fontFamily": "Arial, sans-serif", "color": "#2ecc71", "backgroundColor": "transparent", "rotation": 0 },
                
                // ===== INTERFACE LABELS - ATTACHED TO LINK =====
                { "id": "text_if_pe1", "type": "text", "x": 0, "y": 0, "text": "ge400-0/0/4.210", "fontSize": "14px", "fontFamily": "Consolas, monospace", "color": "#2ecc71", "backgroundColor": "transparent", "rotation": 0, "attachedTo": "link_l2", "attachmentSide": "left", "offset": { "x": 50, "y": -20 } },
                { "id": "text_if_pe2", "type": "text", "x": 0, "y": 0, "text": "bundle-100.210", "fontSize": "14px", "fontFamily": "Consolas, monospace", "color": "#2ecc71", "backgroundColor": "transparent", "rotation": 0, "attachedTo": "link_l2", "attachmentSide": "right", "offset": { "x": -50, "y": -20 } },
                { "id": "text_svc", "type": "text", "x": 0, "y": 0, "text": "L2 Service", "fontSize": "12px", "fontFamily": "Arial, sans-serif", "color": "#27ae60", "backgroundColor": "transparent", "rotation": 0, "attachedTo": "link_l2", "attachmentSide": "middle", "offset": { "x": 0, "y": -20 } },
                
                // ===== DEVICE IPs =====
                { "id": "text_pe1_ip", "type": "text", "x": 200, "y": 440, "text": "100.64.2.33", "fontSize": "12px", "fontFamily": "Consolas, monospace", "color": "#7f8c8d", "backgroundColor": "transparent", "rotation": 0 },
                { "id": "text_pe2_ip", "type": "text", "x": 1100, "y": 440, "text": "100.64.0.220", "fontSize": "12px", "fontFamily": "Consolas, monospace", "color": "#7f8c8d", "backgroundColor": "transparent", "rotation": 0 }
            ],
            "metadata": { "deviceIdCounter": 2, "linkIdCounter": 1, "textIdCounter": 7, "description": "Logical view - sub-interfaces attached to link" }
        };
    },

    /**
     * PHYSICAL VIEW: Full hierarchical path with DNAAS leaf switches and fabric
     * Includes all interfaces, sub-interfaces, bundles, and VLAN manipulation
     */
    getDnaasBD210Topology() {
        return {
            "version": "1.0",
            "objects": [
                // ═══════════════════════════════════════════════════════════════════
                // DEVICES - Hierarchical Layout (3 tiers, wider spacing)
                // ═══════════════════════════════════════════════════════════════════
                
                // TIER 1: Provider Edge Routers
                { "id": "device_pe1", "type": "device", "deviceType": "router", "x": 100, "y": 380, "radius": 50, "rotation": 0, "color": "#3498db", "label": "YOR_PE-1", "locked": false, "visualStyle": "classic" },
                { "id": "device_pe2", "type": "device", "deviceType": "router", "x": 1100, "y": 380, "radius": 50, "rotation": 0, "color": "#3498db", "label": "YOR_PE-2", "locked": false, "visualStyle": "classic" },
                
                // TIER 2: DNAAS Leaf Switches
                { "id": "device_leaf_d16", "type": "device", "deviceType": "router", "x": 320, "y": 380, "radius": 42, "rotation": 0, "color": "#FF5E1F", "label": "DNAAS-LEAF-D16", "locked": false, "visualStyle": "server" },
                { "id": "device_leaf_b15", "type": "device", "deviceType": "router", "x": 880, "y": 380, "radius": 42, "rotation": 0, "color": "#FF5E1F", "label": "DNAAS-LEAF-B15", "locked": false, "visualStyle": "server" },
                
                // TIER 3: DNAAS Fabric Core
                { "id": "device_spine1", "type": "device", "deviceType": "router", "x": 500, "y": 180, "radius": 38, "rotation": 0, "color": "#9b59b6", "label": "SPINE-1", "locked": false, "visualStyle": "server" },
                { "id": "device_spine2", "type": "device", "deviceType": "router", "x": 700, "y": 180, "radius": 38, "rotation": 0, "color": "#9b59b6", "label": "SPINE-2", "locked": false, "visualStyle": "server" },
                
                // ═══════════════════════════════════════════════════════════════════
                // LINKS - Full path with complete interface details
                // ═══════════════════════════════════════════════════════════════════
                
                // PE-1 → DNAAS-LEAF-D16
                { "id": "link_pe1_d16", "type": "link", "originType": "QL", "device1": "device_pe1", "device2": "device_leaf_d16", "color": "#3498db",
                  "start": { "x": 150, "y": 380 }, "end": { "x": 278, "y": 380 }, "style": "solid", "width": 4,
                  "linkDetails": {
                    "interfaceA": "ge400-0/0/4", "interfaceB": "ge100-0/0/4",
                    "subInterfaceA": "ge400-0/0/4.210", "subInterfaceB": "ge100-0/0/4.210",
                    "vlanIdA": 210, "vlanIdB": 210, "vlanMatch": true,
                    "vlanStack": "210", "vlanAction": "none", "innerVlan": "", "outerVlan": "210",
                    "networkType": "L2VPN-EVPN", "bridgeDomain": "g_yor_v210",
                    "description": "PE-1 to DNAAS-LEAF-D16 access link"
                  }
                },
                
                // DNAAS-LEAF-D16 → DNAAS-SPINE-1
                { "id": "link_d16_spine1", "type": "link", "originType": "QL", "device1": "device_leaf_d16", "device2": "device_spine1", "color": "#FF5E1F",
                  "start": { "x": 345, "y": 338 }, "end": { "x": 480, "y": 218 }, "style": "solid", "width": 3,
                  "linkDetails": {
                    "interfaceA": "Bundle-Ether60000", "interfaceB": "Bundle-Ether60001",
                    "subInterfaceA": "Bundle-Ether60000.210", "subInterfaceB": "Bundle-Ether60001.210",
                    "vlanIdA": 210, "vlanIdB": 210, "vlanMatch": true,
                    "vlanStack": "210", "vlanAction": "translate", "innerVlan": "210", "outerVlan": "3210",
                    "networkType": "VXLAN-Fabric", "bridgeDomain": "g_yor_v210",
                    "description": "Leaf-D16 to Spine-1 fabric uplink"
                  }
                },
                
                // DNAAS-LEAF-D16 → DNAAS-SPINE-2 (ECMP)
                { "id": "link_d16_spine2", "type": "link", "originType": "QL", "device1": "device_leaf_d16", "device2": "device_spine2", "color": "#FF5E1F",
                  "start": { "x": 362, "y": 338 }, "end": { "x": 680, "y": 218 }, "style": "dashed", "width": 3,
                  "linkDetails": {
                    "interfaceA": "Bundle-Ether60000", "interfaceB": "Bundle-Ether60002",
                    "subInterfaceA": "Bundle-Ether60000.210", "subInterfaceB": "Bundle-Ether60002.210",
                    "vlanIdA": 210, "vlanIdB": 210, "vlanMatch": true,
                    "vlanStack": "210", "vlanAction": "translate", "innerVlan": "210", "outerVlan": "3210",
                    "networkType": "VXLAN-Fabric", "bridgeDomain": "g_yor_v210",
                    "description": "Leaf-D16 to Spine-2 fabric uplink (ECMP)"
                  }
                },
                
                // DNAAS-SPINE-1 ↔ DNAAS-SPINE-2 (ISL)
                { "id": "link_spine_spine", "type": "link", "originType": "QL", "device1": "device_spine1", "device2": "device_spine2", "color": "#9b59b6",
                  "start": { "x": 538, "y": 180 }, "end": { "x": 662, "y": 180 }, "style": "solid", "width": 5,
                  "linkDetails": {
                    "interfaceA": "Bundle-Ether99999", "interfaceB": "Bundle-Ether99999",
                    "subInterfaceA": "Bundle-Ether99999.0", "subInterfaceB": "Bundle-Ether99999.0",
                    "vlanIdA": 0, "vlanIdB": 0, "vlanMatch": true,
                    "vlanStack": "native", "vlanAction": "none", "innerVlan": "", "outerVlan": "",
                    "networkType": "Fabric-ISL", "bridgeDomain": "fabric-core",
                    "description": "Spine-to-Spine Inter-Switch Link"
                  }
                },
                
                // DNAAS-SPINE-1 → DNAAS-LEAF-B15
                { "id": "link_spine1_b15", "type": "link", "originType": "QL", "device1": "device_spine1", "device2": "device_leaf_b15", "color": "#FF5E1F",
                  "start": { "x": 520, "y": 218 }, "end": { "x": 838, "y": 338 }, "style": "dashed", "width": 3,
                  "linkDetails": {
                    "interfaceA": "Bundle-Ether60003", "interfaceB": "Bundle-Ether60000",
                    "subInterfaceA": "Bundle-Ether60003.210", "subInterfaceB": "Bundle-Ether60000.210",
                    "vlanIdA": 210, "vlanIdB": 210, "vlanMatch": true,
                    "vlanStack": "210", "vlanAction": "translate", "innerVlan": "3210", "outerVlan": "210",
                    "networkType": "VXLAN-Fabric", "bridgeDomain": "g_yor_v210",
                    "description": "Spine-1 to Leaf-B15 fabric downlink"
                  }
                },
                
                // DNAAS-SPINE-2 → DNAAS-LEAF-B15 (ECMP)
                { "id": "link_spine2_b15", "type": "link", "originType": "QL", "device1": "device_spine2", "device2": "device_leaf_b15", "color": "#FF5E1F",
                  "start": { "x": 720, "y": 218 }, "end": { "x": 855, "y": 338 }, "style": "solid", "width": 3,
                  "linkDetails": {
                    "interfaceA": "Bundle-Ether60004", "interfaceB": "Bundle-Ether60000",
                    "subInterfaceA": "Bundle-Ether60004.210", "subInterfaceB": "Bundle-Ether60000.210",
                    "vlanIdA": 210, "vlanIdB": 210, "vlanMatch": true,
                    "vlanStack": "210", "vlanAction": "translate", "innerVlan": "3210", "outerVlan": "210",
                    "networkType": "VXLAN-Fabric", "bridgeDomain": "g_yor_v210",
                    "description": "Spine-2 to Leaf-B15 fabric downlink (ECMP)"
                  }
                },
                
                // DNAAS-LEAF-B15 → PE-2
                { "id": "link_b15_pe2", "type": "link", "originType": "QL", "device1": "device_leaf_b15", "device2": "device_pe2", "color": "#3498db",
                  "start": { "x": 922, "y": 380 }, "end": { "x": 1050, "y": 380 }, "style": "solid", "width": 4,
                  "linkDetails": {
                    "interfaceA": "Bundle-Ether100", "interfaceB": "Bundle-Ether100",
                    "subInterfaceA": "Bundle-Ether100.210", "subInterfaceB": "Bundle-Ether100.210",
                    "vlanIdA": 210, "vlanIdB": 210, "vlanMatch": true,
                    "vlanStack": "210", "vlanAction": "none", "innerVlan": "", "outerVlan": "210",
                    "networkType": "L2VPN-EVPN", "bridgeDomain": "g_yor_v210",
                    "description": "DNAAS-LEAF-B15 to PE-2 access link"
                  }
                },
                
                // ═══════════════════════════════════════════════════════════════════
                // TEXT LABELS
                // ═══════════════════════════════════════════════════════════════════
                
                // Main Title
                { "id": "text_title", "type": "text", "x": 600, "y": 50, "text": "BD: g_yor_v210 (VLAN 210)", "fontSize": "20px", "fontFamily": "Arial, sans-serif", "color": "#2ecc71", "backgroundColor": "#1a1a2e", "rotation": 0 },
                { "id": "text_subtitle", "type": "text", "x": 600, "y": 78, "text": "EVPN/VXLAN L2VPN Service Path", "fontSize": "12px", "fontFamily": "Arial, sans-serif", "color": "#95a5a6", "backgroundColor": "#1a1a2e", "rotation": 0 },
                
                // Interface Labels
                { "id": "text_if_pe1", "type": "text", "x": 165, "y": 355, "text": "ge400-0/0/4.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#5dade2", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_d16_in", "type": "text", "x": 255, "y": 355, "text": "ge100-0/0/4.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#f0b27a", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_d16_up", "type": "text", "x": 380, "y": 300, "text": "Be60000.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#f0b27a", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_spine1_dn", "type": "text", "x": 460, "y": 235, "text": "Be60001.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#bb8fce", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_spine_isl", "type": "text", "x": 600, "y": 160, "text": "ISL (native)", "fontSize": "8px", "fontFamily": "monospace", "color": "#bb8fce", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_spine2_dn", "type": "text", "x": 740, "y": 235, "text": "Be60004.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#bb8fce", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_b15_up", "type": "text", "x": 820, "y": 300, "text": "Be60000.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#f0b27a", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_b15_out", "type": "text", "x": 935, "y": 355, "text": "Be100.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#f0b27a", "backgroundColor": "#1a252e", "rotation": 0 },
                { "id": "text_if_pe2", "type": "text", "x": 1035, "y": 355, "text": "Be100.210", "fontSize": "8px", "fontFamily": "monospace", "color": "#5dade2", "backgroundColor": "#1a252e", "rotation": 0 },
                
                // VLAN Tags
                { "id": "text_vlan_pe1_d16", "type": "text", "x": 210, "y": 400, "text": "V:210", "fontSize": "8px", "fontFamily": "monospace", "color": "#2ecc71", "backgroundColor": "transparent", "rotation": 0 },
                { "id": "text_vlan_fabric", "type": "text", "x": 600, "y": 120, "text": "Fabric: VLAN 3210", "fontSize": "9px", "fontFamily": "monospace", "color": "#FF7A33", "backgroundColor": "#1a1a2e", "rotation": 0 },
                { "id": "text_vlan_b15_pe2", "type": "text", "x": 990, "y": 400, "text": "V:210", "fontSize": "8px", "fontFamily": "monospace", "color": "#2ecc71", "backgroundColor": "transparent", "rotation": 0 },
                
                // VLAN Path
                { "id": "text_vlan_path", "type": "text", "x": 600, "y": 480, "text": "VLAN Path: PE-1(210) → D16(210→3210) → SPINE(3210) → B15(3210→210) → PE-2(210)", "fontSize": "10px", "fontFamily": "monospace", "color": "#ecf0f1", "backgroundColor": "#2c3e50", "rotation": 0 },
                
                // Tier labels
                { "id": "text_tier_pe", "type": "text", "x": 40, "y": 380, "text": "PE", "fontSize": "10px", "fontFamily": "Arial, sans-serif", "color": "#3498db", "backgroundColor": "transparent", "rotation": 0 },
                { "id": "text_tier_spine", "type": "text", "x": 40, "y": 180, "text": "SPINE", "fontSize": "10px", "fontFamily": "Arial, sans-serif", "color": "#9b59b6", "backgroundColor": "transparent", "rotation": 0 }
            ],
            "metadata": { 
                "deviceIdCounter": 6, 
                "linkIdCounter": 7, 
                "textIdCounter": 20, 
                "description": "DNAAS L2VPN Path - BD g_yor_v210 with validated VLAN matching"
            }
        };
    }
};

console.log('[topology-sample-data.js] SampleTopologyData loaded');
