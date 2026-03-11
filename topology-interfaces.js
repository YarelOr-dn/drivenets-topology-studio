/**
 * topology-interfaces.js - Interface Generation Module
 * 
 * Extracted from topology.js for modular architecture.
 * Contains interface generation functions for different platform types.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.InterfaceGenerator = {

    // Interface configurations based on Confluence NCP Cheat Sheet
    interfaceConfigs: {
        // NCP1 - J2 chip - 40x100G NIF
        'SA-40C': [
            { prefix: 'ge100', start: 0, count: 40 }
        ],
        // NCP2 - J2 chip - 10x400G NIF  
        'SA-10CD': [
            { prefix: 'ge400', start: 0, count: 10 }
        ],
        // NCP3 - J2C+ chip - 36x400G NIF (32 usable with KBP)
        'SA-36CD-S': [
            { prefix: 'ge400', start: 0, count: 36 }
        ],
        // NCP3-SA - J2C+ chip - 36x400G NIF standalone
        'SA-36CD-S-SA': [
            { prefix: 'ge400', start: 0, count: 36 }
        ],
        // NCPL - J2C chip - 64x10G + 12x100G NIF
        'SA-64X12C-S': [
            { prefix: 'ge10', start: 0, count: 64 },
            { prefix: 'ge100', start: 64, count: 12 }
        ],
        // NCPL-SA - J2C chip - 64x10G + 8x100G NIF
        'SA-64X8C-S': [
            { prefix: 'ge10', start: 0, count: 64 },
            { prefix: 'ge100', start: 64, count: 8 }
        ],
        // NCP5 - J3AI chip - 18x800G NIF
        'SA-38E': [
            { prefix: 'ge800', start: 0, count: 18 }
        ],
        // NCP6 - Q2C+ chip - 4x10G + 40x100G + 8x400G NIF
        'SA-40C8CD': [
            { prefix: 'ge10', start: 48, count: 4 },
            { prefix: 'ge100', start: 0, count: 40 },
            { prefix: 'ge400', start: 40, count: 8 }
        ],
        // NCP6-S - Q2C+ chip - 4x10G + 40x100G + 6x400G NIF
        'SA-40C6CD-S': [
            { prefix: 'ge10', start: 46, count: 4 },
            { prefix: 'ge100', start: 0, count: 40 },
            { prefix: 'ge400', start: 40, count: 6 }
        ],
        // NCP9-S - Q2C chip - 96x10G + 6x100G NIF
        'SA-96X6C-S': [
            { prefix: 'ge10', start: 0, count: 96 },
            { prefix: 'ge100', start: 96, count: 6 }
        ],
        // NCP10 - Q3D chip - 32x800G NIF
        'SA-32E-S': [
            { prefix: 'ge800', start: 0, count: 32 }
        ],
        // CS1 - Cisco Silicon - 32x400G NIF
        'SA-32CD': [
            { prefix: 'ge400', start: 0, count: 32 }
        ]
    },

    /**
     * Generate interfaces for a given platform
     */
    generateInterfaces(platformOfficial) {
        const config = this.interfaceConfigs[platformOfficial];
        if (!config) {
            // Default fallback
            return ['ge100-0/0/0', 'ge100-0/0/1', 'mgmt0', 'Loopback0'];
        }
        
        const interfaces = [];
        
        // Generate interfaces based on config
        for (const portGroup of config) {
            for (let i = 0; i < portGroup.count; i++) {
                const portNum = portGroup.start + i;
                interfaces.push(`${portGroup.prefix}-0/0/${portNum}`);
            }
        }
        
        // Add management and loopback interfaces
        interfaces.push('mgmt0');
        interfaces.push('Loopback0');
        
        return interfaces;
    },

    /**
     * Generate interfaces for Cluster platforms
     * Clusters use NCP interfaces with ncp-id prefix: ge{speed}-{ncp-id}/0/{port}
     */
    generateClusterInterfaces(clusterPlatform) {
        const interfaces = [];
        
        // Get the NCP type for this cluster
        let ncpType = 'SA-40C'; // Default
        if (clusterPlatform && clusterPlatform.ncpType) {
            ncpType = clusterPlatform.ncpType;
        }
        
        // Get base platform interfaces
        const baseInterfaces = this.generateInterfaces(ncpType);
        
        // For clusters, show interfaces from first 4 NCPs
        const maxNcps = 4;
        for (let ncpId = 0; ncpId < maxNcps; ncpId++) {
            for (const intf of baseInterfaces) {
                if (intf.startsWith('ge')) {
                    // Replace 0/ with ncp-id/
                    const clusterIntf = intf.replace('-0/', `-${ncpId}/`);
                    interfaces.push(clusterIntf);
                }
            }
        }
        
        // Add Bundle interfaces (LAG)
        for (let bundle = 1; bundle <= 8; bundle++) {
            interfaces.push(`Bundle-${bundle}`);
        }
        
        // Add common interfaces
        interfaces.push('mgmt0');
        interfaces.push('Loopback0');
        
        return interfaces;
    },

    /**
     * Generate interfaces for NC-AI platforms
     * NC-AI uses distributed SA nodes with their own interfaces
     */
    generateAIInterfaces(aiPlatform) {
        const interfaces = [];
        
        // Determine port configuration based on platform speed
        let prefix = 'ge400';
        let portCount = 32;
        
        if (aiPlatform && aiPlatform.nifSpeed === '800G') {
            prefix = 'ge800';
            portCount = 18; // SA-38E has 18x800G NIF
        } else if (aiPlatform && aiPlatform.nifSpeed === '400G') {
            prefix = 'ge400';
            portCount = 36; // SA-36CD-S has 36x400G NIF
        }
        
        // Generate NIF interfaces for first few nodes
        const maxNodes = 4;
        for (let nodeId = 0; nodeId < maxNodes; nodeId++) {
            for (let port = 0; port < Math.min(portCount, 8); port++) {
                interfaces.push(`${prefix}-${nodeId}/0/${port}`);
            }
        }
        
        // Add Bundle interfaces
        for (let bundle = 1; bundle <= 4; bundle++) {
            interfaces.push(`Bundle-${bundle}`);
        }
        
        // Add common interfaces
        interfaces.push('mgmt0');
        interfaces.push('Loopback0');
        
        return interfaces;
    },

    /**
     * Generate interfaces for DNAAS platforms (NCM devices)
     */
    generateDNAASInterfaces(platform) {
        const interfaces = [];
        
        if (!platform || !platform.nif) {
            // Default interfaces for NCM devices
            for (let port = 0; port < 12; port++) {
                interfaces.push(`ge100-0/0/${port}`);
            }
            return interfaces;
        }
        
        // Generate based on NIF (Network Interface) configuration
        const nif = platform.nif;
        const speed = nif.speed || '100G';
        const count = nif.count || 12;
        
        // Determine interface prefix based on speed
        let prefix = 'ge100'; // Default 100G
        if (speed === '400G') prefix = 'ge400';
        else if (speed === '10G') prefix = 'ge10';
        else if (speed === '25G') prefix = 'ge25';
        else if (speed === '800G') prefix = 'ge800';
        
        // Generate interfaces: ge{speed}-0/0/{port}
        for (let port = 0; port < count; port++) {
            interfaces.push(`${prefix}-0/0/${port}`);
        }
        
        // Also add FIF (Fabric Interface) ports if available
        if (platform.fif) {
            const fifSpeed = platform.fif.speed || '400G';
            const fifCount = platform.fif.count || 4;
            let fifPrefix = fifSpeed === '400G' ? 'ge400' : (fifSpeed === '800G' ? 'ge800' : 'ge100');
            
            for (let port = 0; port < fifCount; port++) {
                interfaces.push(`${fifPrefix}-0/1/${port}`);
            }
        }
        
        return interfaces;
    },

    /**
     * Get interfaces for a platform based on category
     */
    getInterfacesForPlatform(editor, platformOfficial, category) {
        if (category === 'SA') {
            return this.generateInterfaces(platformOfficial);
        } else if (category === 'CL') {
            const platform = editor.driveNetsPlatforms?.CL?.platforms?.find(p => p.official === platformOfficial);
            return this.generateClusterInterfaces(platform);
        } else if (category === 'NC-AI') {
            const platform = editor.driveNetsPlatforms?.['NC-AI']?.platforms?.find(p => p.official === platformOfficial);
            return this.generateAIInterfaces(platform || {});
        } else if (category === 'DNAAS') {
            const platform = editor.driveNetsPlatforms?.DNAAS?.platforms?.find(p => p.official === platformOfficial);
            return this.generateDNAASInterfaces(platform || {});
        }
        return [];
    },

    /**
     * Extract interfaces and sub-interfaces from config text
     */
    extractInterfacesFromConfig(configText) {
        const interfaces = [];
        const subInterfaces = [];
        
        const lines = configText.split('\n');
        let inInterfacesSection = false;
        let currentInterface = null;
        let currentVlan = null;
        let indentLevel = 0;
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            if (trimmed === 'interfaces') {
                inInterfacesSection = true;
                indentLevel = line.search(/\S/);
                continue;
            }
            
            if (inInterfacesSection && line.match(/^\S/) && trimmed !== '!') {
                inInterfacesSection = false;
                currentInterface = null;
            }
            
            if (!inInterfacesSection) continue;
            
            const interfaceMatch = trimmed.match(/^(ge\d+-\d+\/\d+\/\d+|Bundle-Ether\d+|bundle-\d+|Loopback\d+|mgmt\d+)(?:\.(\d+))?$/i);
            if (interfaceMatch) {
                const intfName = interfaceMatch[1];
                const subId = interfaceMatch[2];
                
                if (subId) {
                    currentInterface = `${intfName}.${subId}`;
                    subInterfaces.push({
                        name: currentInterface,
                        parent: intfName,
                        subId: parseInt(subId),
                        vlanId: null
                    });
                } else {
                    currentInterface = intfName;
                    if (!interfaces.find(i => i.name === intfName)) {
                        interfaces.push({
                            name: intfName,
                            subInterfaces: []
                        });
                    }
                }
                currentVlan = null;
                continue;
            }
            
            const vlanMatch = trimmed.match(/^vlan-id\s+(\d+)/);
            if (vlanMatch && currentInterface) {
                const vlanId = parseInt(vlanMatch[1]);
                const subIntf = subInterfaces.find(s => s.name === currentInterface);
                if (subIntf) {
                    subIntf.vlanId = vlanId;
                }
            }
        }
        
        for (const subIntf of subInterfaces) {
            const parent = interfaces.find(i => i.name === subIntf.parent);
            if (parent) {
                parent.subInterfaces.push(subIntf);
            }
        }
        
        return { interfaces, subInterfaces };
    },

    /**
     * Get sub-interfaces with a specific VLAN ID
     */
    getSubInterfacesWithVlan(configData, vlanId) {
        if (!configData || !configData.subInterfaces) return [];
        return configData.subInterfaces.filter(s => s.vlanId === vlanId);
    },

    /**
     * Extract VLAN ID from a sub-interface name (e.g., "ge400-0/0/4.210" -> 210)
     */
    extractVlanFromSubInterface(subInterfaceName) {
        if (!subInterfaceName) return null;
        const match = subInterfaceName.match(/\.(\d+)$/);
        return match ? parseInt(match[1]) : null;
    },

    /**
     * Validate that two sub-interfaces have matching VLANs
     */
    validateVlanMatch(subInterfaceA, subInterfaceB) {
        const vlanA = this.extractVlanFromSubInterface(subInterfaceA);
        const vlanB = this.extractVlanFromSubInterface(subInterfaceB);
        
        if (vlanA === null || vlanB === null) {
            return { match: false, vlanA, vlanB, reason: 'Could not extract VLAN' };
        }
        
        return {
            match: vlanA === vlanB,
            vlanA,
            vlanB,
            reason: vlanA === vlanB ? 'VLANs match' : `VLAN mismatch: ${vlanA} vs ${vlanB}`
        };
    }
};

console.log('[topology-interfaces.js] InterfaceGenerator loaded');
