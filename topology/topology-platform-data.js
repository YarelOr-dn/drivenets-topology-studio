// ============================================================================
// TOPOLOGY PLATFORM DATA
// ============================================================================
// DriveNets platform and transceiver databases.
// Source: Confluence NCP Cheat Sheet, NC/NC-AI Model/SKU, Transceiver Templates
//
// Usage:
//   const platformData = new PlatformData();
//   platformData.getPlatform('SA-40C');
//   platformData.getTransceiversForSpeed('400G');
//   platformData.generateInterfaces('SA-36CD-S');
// ============================================================================

class PlatformData {
    constructor() {
        this._initPlatforms();
        this._initTransceivers();
        this._initInterfaceMap();
    }

    // ========== DRIVENETS PLATFORM DATABASE ==========
    // Source: Confluence NCP Cheat Sheet (page 5531501013) and NC/NC-AI Model/SKU (page 4235299842)
    // Updated: December 2024
    _initPlatforms() {
        this.platforms = {
            // SA (Standalone) Platforms - From Confluence NCP Cheat Sheet
            SA: {
                category: 'SA',
                platforms: [
                    { 
                        displayName: 'NCP1 (SA-40C)', 
                        official: 'SA-40C', 
                        chip: 'J2', 
                        hwModel: 'S9700-53DX',
                        nif: { count: 40, speed: '100G' },
                        fif: { count: 13, speed: '400G' },
                        vendor: 'UFI',
                        interfaces: null // Generated on demand
                    },
                    { 
                        displayName: 'NCP2 (SA-10CD)', 
                        official: 'SA-10CD', 
                        chip: 'J2', 
                        hwModel: 'S9700-23D',
                        nif: { count: 10, speed: '400G' },
                        fif: { count: 13, speed: '400G' },
                        vendor: 'UFI',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP3 (SA-36CD-S)', 
                        official: 'SA-36CD-S', 
                        chip: 'J2C+', 
                        hwModel: 'S9710-76D',
                        nif: { count: 36, speed: '400G' },
                        fif: { count: 40, speed: '400G' },
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP3-SA (SA-36CD-S-SA)', 
                        official: 'SA-36CD-S-SA', 
                        chip: 'J2C+', 
                        hwModel: 'S9610-36D',
                        nif: { count: 36, speed: '400G' },
                        fif: null,
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCPL (SA-64X12C-S)', 
                        official: 'SA-64X12C-S', 
                        chip: 'J2C', 
                        hwModel: 'S9701-82DC',
                        nif: [
                            { count: 64, speed: '10G' },
                            { count: 12, speed: '100G' }
                        ],
                        fif: { count: 6, speed: '400G' },
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCPL-SA (SA-64X8C-S)', 
                        official: 'SA-64X8C-S', 
                        chip: 'J2C', 
                        hwModel: 'S9600-72XC',
                        nif: [
                            { count: 64, speed: '10G' },
                            { count: 8, speed: '100G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP5 (SA-38E)', 
                        official: 'SA-38E', 
                        chip: 'J3AI', 
                        hwModel: 'ASA926-18XKE',
                        nif: { count: 18, speed: '800G' },
                        fif: { count: 20, speed: '800G' },
                        vendor: 'ACCTON',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP6 (SA-40C8CD)', 
                        official: 'SA-40C8CD', 
                        chip: 'Q2C+', 
                        hwModel: 'S9610-48DX',
                        nif: [
                            { count: 4, speed: '10G' },
                            { count: 40, speed: '100G' },
                            { count: 8, speed: '400G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        gearbox: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP6-S (SA-40C6CD-S)', 
                        official: 'SA-40C6CD-S', 
                        chip: 'Q2C+', 
                        hwModel: 'S9610-46DX',
                        nif: [
                            { count: 4, speed: '10G' },
                            { count: 40, speed: '100G' },
                            { count: 6, speed: '400G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        gearbox: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP9-S (SA-96X6C-S)', 
                        official: 'SA-96X6C-S', 
                        chip: 'Q2C', 
                        hwModel: 'S9601-102XC-R',
                        nif: [
                            { count: 96, speed: '10G' },
                            { count: 6, speed: '100G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP10 (SA-32E-S)', 
                        official: 'SA-32E-S', 
                        chip: 'Q3D', 
                        hwModel: 'S9620-32E',
                        nif: { count: 32, speed: '800G' },
                        fif: null,
                        vendor: 'UFI',
                        interfaces: null
                    },
                    { 
                        displayName: 'CS1 (SA-32CD)', 
                        official: 'SA-32CD', 
                        chip: 'CS1', 
                        hwModel: 'AS9286-32D',
                        nif: { count: 32, speed: '400G' },
                        fif: null,
                        vendor: 'ACCTON',
                        interfaces: null
                    }
                ]
            },
            // CL (Cluster) Platforms - From Confluence
            CL: {
                category: 'CL',
                platforms: [
                    { displayName: 'CL-16', official: 'CL-16', nodes: 16, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-32', official: 'CL-32', nodes: 32, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-48', official: 'CL-48', nodes: 48, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-49', official: 'CL-49', nodes: 49, ncpType: 'SA-64X12C-S', interfaces: null },
                    { displayName: 'CL-51', official: 'CL-51', nodes: 51, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-64', official: 'CL-64', nodes: 64, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-76', official: 'CL-76', nodes: 76, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-86', official: 'CL-86', nodes: 86, ncpType: 'SA-64X12C-S', interfaces: null },
                    { displayName: 'CL-96', official: 'CL-96', nodes: 96, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-134', official: 'CL-134', nodes: 134, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-153', official: 'CL-153', nodes: 153, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-192', official: 'CL-192', nodes: 192, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-409', official: 'CL-409', nodes: 409, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-768', official: 'CL-768', nodes: 768, ncpType: 'SA-40C', interfaces: null }
                ]
            },
            // NC-AI (Network Cloud AI) Clusters - From Confluence NC-AI Architecture
            'NC-AI': {
                category: 'NC-AI',
                platforms: [
                    { displayName: 'AI-72-400G', official: 'AI-72-400G', nifCount: 72, nifSpeed: '400G', gen: 1, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-72-800G-2', official: 'AI-72-800G-2', nifCount: 72, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-216-800G-2', official: 'AI-216-800G-2', nifCount: 216, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-576-800G-2', official: 'AI-576-800G-2', nifCount: 576, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-768-400G-1', official: 'AI-768-400G-1', nifCount: 768, nifSpeed: '400G', gen: 1, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'AI-1152-800G-2', official: 'AI-1152-800G-2', nifCount: 1152, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-2016-800G-2', official: 'AI-2016-800G-2', nifCount: 2016, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-2304-800G-2', official: 'AI-2304-800G-2', nifCount: 2304, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-8192-400G-1', official: 'AI-8192-400G-1', nifCount: 8192, nifSpeed: '400G', gen: 1, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'AI-8192-400G-2', official: 'AI-8192-800G-2', nifCount: 8192, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null }
                ]
            },
            // DNAAS (Disaggregated Network As A Service) - NCM Fabric Devices
            // NCM = Network Cloud Module - building blocks for DNAAS fabric
            DNAAS: {
                category: 'DNAAS',
                platforms: [
                    { 
                        displayName: 'NCM-1600', 
                        official: 'NCM-1600', 
                        description: 'High-capacity NCM for large DNAAS deployments',
                        chip: 'J2', 
                        nif: { count: 48, speed: '100G' },
                        fif: { count: 16, speed: '400G' },
                        interfaces: null
                    },
                    { 
                        displayName: 'NCM-460', 
                        official: 'NCM-460', 
                        description: 'Mid-range NCM for medium DNAAS deployments',
                        chip: 'J2', 
                        nif: { count: 24, speed: '100G' },
                        fif: { count: 8, speed: '400G' },
                        interfaces: null
                    },
                    { 
                        displayName: 'NCM-200', 
                        official: 'NCM-200', 
                        description: 'Entry-level NCM for small DNAAS deployments',
                        chip: 'J', 
                        nif: { count: 12, speed: '100G' },
                        fif: { count: 4, speed: '400G' },
                        interfaces: null
                    },
                    { 
                        displayName: 'NCC-2500', 
                        official: 'NCC-2500', 
                        description: 'Network Cloud Controller - Large',
                        chip: 'Controller',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCC-1500', 
                        official: 'NCC-1500', 
                        description: 'Network Cloud Controller - Medium',
                        chip: 'Controller',
                        interfaces: null
                    }
                ]
            }
        };
    }

    // ========== TRANSCEIVER DATABASE ==========
    // Source: Confluence DN Devices Transceiver Templates (page 5624528975)
    // Real transceivers with manufacturer, part numbers, and platform support
    _initTransceivers() {
        this.transceivers = {
            // 1G Transceivers (SFP form factor)
            '1G': [
                { name: '1000BASE-EX SFP', manufacturer: 'Molex', partNumber: '1837024404', type: 'SFP', reach: '40km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-96X6C-S'] },
                { name: '1000BASE-ZX SFP', manufacturer: 'ProLabs', partNumber: 'SFP-1000Base-ZX-ATT', type: 'SFP', reach: '80km', media: 'SMF', wavelength: '1550nm', platforms: ['SA-96X6C-S'] },
                { name: '1000BASE-LX BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-B10U31', type: 'SFP', reach: '10km', media: 'SMF', wavelength: '1310nm TX/1550nm RX', platforms: ['SA-96X6C-S'] },
                { name: '1000BASE-EX BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-A40U31', type: 'SFP', reach: '40km', media: 'SMF', wavelength: '1310nm TX/1550nm RX', platforms: ['SA-96X6C-S'] }
            ],
            // 10G Transceivers (SFP+ form factor)
            '10G': [
                { name: '10GBASE-LR SFP+', manufacturer: 'Coherent', partNumber: 'FTLX1475D3BCL', type: 'SFP+', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S', 'SA-64X12C-S'] },
                { name: '10GBASE-ER SFP+', manufacturer: 'ProLabs', partNumber: 'SFP-10Gbase-ER-ATT', type: 'SFP+', reach: '40km', media: 'SMF', wavelength: '1550nm', platforms: ['SA-96X6C-S'] },
                { name: '10GBASE-ZR SFP+', manufacturer: 'ProLabs', partNumber: 'SFP-10Gbase-ZR-ATT', type: 'SFP+', reach: '80km', media: 'SMF', wavelength: '1550nm', platforms: ['SA-96X6C-S'] },
                { name: '10GBASE-LR BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-S10U27', type: 'SFP+', reach: '10km', media: 'SMF', wavelength: '1270nm TX/1330nm RX', platforms: ['SA-96X6C-S'] },
                { name: '10GBASE-ER BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-S40U27', type: 'SFP+', reach: '40km', media: 'SMF', wavelength: '1270nm TX/1330nm RX', platforms: ['SA-96X6C-S'] },
                { name: 'Rate Adapter 1G-10G', manufacturer: 'Arista', partNumber: 'SFP-10G-RA-1G-LX', type: 'SFP+', reach: '5km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-40C6CD-S'] }
            ],
            // 100G Transceivers (QSFP28 form factor)
            '100G': [
                { name: '100GBASE-LR QSFP28', manufacturer: 'Molex', partNumber: '1064273710', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '100GBASE-LR4 QSFP28', manufacturer: 'Coherent', partNumber: 'FTLC1154RDPL', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-LR4 QSFP28 Gen3', manufacturer: 'Coherent', partNumber: 'FTLC1156RDPL', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-LR4 QSFP28', manufacturer: 'Molex', partNumber: '1837104011', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-ER4 QSFP28', manufacturer: 'Nokia', partNumber: '3HE11239AA', type: 'QSFP28', reach: '30km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-ZR4 QSFP28', manufacturer: 'Nokia', partNumber: '3HE19472AA', type: 'QSFP28', reach: '80km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-ZR DCO QSFP28', manufacturer: 'Coherent', partNumber: 'FTLC3353S3PL1', type: 'QSFP28', reach: '80km+', media: 'SMF', wavelength: 'C-band 1550nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] }
            ],
            // 400G Transceivers (QSFP-DD form factor)
            '400G': [
                { name: '400GBASE-LR4 QSFP-DD', manufacturer: 'Coherent', partNumber: 'FTCD4323E3PCL-1Y', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: 'CWDM4 1310nm', platforms: ['SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '4x100G-LR1 PSM QSFP-DD', manufacturer: 'Innolight', partNumber: 'T-DP4CNL-N00', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-36CD-S-SA'] },
                { name: '400GBASE-ZR+ DCO QSFP-DD', manufacturer: 'Ciena', partNumber: '176-3370-9P0', type: 'QSFP-DD', reach: '600km+', media: 'SMF', wavelength: 'C-band 1550nm', platforms: ['SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '400GBASE-ZR+ DCO QSFP-DD', manufacturer: 'Coherent', partNumber: 'FTCD3323R1PCL-1Y', type: 'QSFP-DD', reach: '600km', media: 'SMF', wavelength: 'C-band 1550nm', platforms: ['SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '400GBASE-DR4 QSFP-DD', manufacturer: 'Generic', partNumber: 'QSFP-DD-400G-DR4', type: 'QSFP-DD', reach: '500m', media: 'SMF', wavelength: '1310nm', platforms: ['SA-36CD-S', 'SA-36CD-S-SA', 'SA-40C6CD-S', 'SA-32CD'] },
                { name: '400GBASE-FR4 QSFP-DD', manufacturer: 'Generic', partNumber: 'QSFP-DD-400G-FR4', type: 'QSFP-DD', reach: '2km', media: 'SMF', wavelength: 'CWDM', platforms: ['SA-36CD-S', 'SA-36CD-S-SA', 'SA-40C6CD-S', 'SA-32CD'] }
            ],
            // 800G Transceivers (OSFP / QSFP-DD800 form factor)
            '800G': [
                { name: '8x100G-LR1 PSM OSFP', manufacturer: 'Innolight', partNumber: 'T-DP8CNL-N00', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-32E-S'] },
                { name: '2x400G-LR4-10 OSFP', manufacturer: 'Innolight', partNumber: 'T-DL8CNL-N00', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: 'CWDM4', platforms: ['SA-32E-S'] },
                { name: '800GBASE-DR8 OSFP', manufacturer: 'Generic', partNumber: 'OSFP-800G-DR8', type: 'OSFP', reach: '500m', media: 'SMF', wavelength: '1310nm', platforms: ['SA-38E', 'SA-32E-S'] },
                { name: '800GBASE-2xFR4 OSFP', manufacturer: 'Generic', partNumber: 'OSFP-800G-2xFR4', type: 'OSFP', reach: '2km', media: 'SMF', wavelength: 'CWDM', platforms: ['SA-38E', 'SA-32E-S'] },
                { name: '800GBASE-2xLR4 OSFP', manufacturer: 'Generic', partNumber: 'OSFP-800G-2xLR4', type: 'OSFP', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM', platforms: ['SA-38E', 'SA-32E-S'] }
            ],
            // Management/Copper
            'MGMT': [
                { name: 'RJ45-1G', manufacturer: 'Generic', partNumber: 'RJ45-1G', type: 'RJ45', reach: '100m', media: 'Copper Cat6', wavelength: 'N/A', platforms: ['all'] },
                { name: 'RJ45-10G', manufacturer: 'Generic', partNumber: 'RJ45-10G', type: 'RJ45', reach: '30m', media: 'Copper Cat6a', wavelength: 'N/A', platforms: ['all'] }
            ]
        };
    }

    // Map interface prefix to transceiver speed category
    _initInterfaceMap() {
        this.interfaceToTransceiverMap = {
            'ge10': '10G',      // 10G interfaces
            'ge25': '25G',      // 25G interfaces  
            'ge100': '100G',    // 100G interfaces
            'ge400': '400G',    // 400G interfaces
            'ge800': '800G',    // 800G interfaces
            'mgmt': 'MGMT',     // Management interfaces
            'Bundle': '100G',   // Bundle/LAG (default to 100G)
            'Loopback': null,   // Loopback - no transceiver
        };

        // Interface configurations based on Confluence NCP Cheat Sheet
        this.interfaceConfigs = {
            'SA-40C': [{ prefix: 'ge100', start: 0, count: 40 }],
            'SA-10CD': [{ prefix: 'ge400', start: 0, count: 10 }],
            'SA-36CD-S': [{ prefix: 'ge400', start: 0, count: 36 }],
            'SA-36CD-S-SA': [{ prefix: 'ge400', start: 0, count: 36 }],
            'SA-64X12C-S': [
                { prefix: 'ge10', start: 0, count: 64 },
                { prefix: 'ge100', start: 64, count: 12 }
            ],
            'SA-64X8C-S': [
                { prefix: 'ge10', start: 0, count: 64 },
                { prefix: 'ge100', start: 64, count: 8 }
            ],
            'SA-38E': [{ prefix: 'ge800', start: 0, count: 18 }],
            'SA-40C8CD': [
                { prefix: 'ge10', start: 48, count: 4 },
                { prefix: 'ge100', start: 0, count: 40 },
                { prefix: 'ge400', start: 40, count: 8 }
            ],
            'SA-40C6CD-S': [
                { prefix: 'ge10', start: 46, count: 4 },
                { prefix: 'ge100', start: 0, count: 40 },
                { prefix: 'ge400', start: 40, count: 6 }
            ],
            'SA-96X6C-S': [
                { prefix: 'ge10', start: 0, count: 96 },
                { prefix: 'ge100', start: 96, count: 6 }
            ],
            'SA-32E-S': [{ prefix: 'ge800', start: 0, count: 32 }],
            'SA-32CD': [{ prefix: 'ge400', start: 0, count: 32 }],
            // NCM platforms
            'NCM-1600': [
                { prefix: 'ge100', start: 0, count: 48 },
                { prefix: 'ge400', start: 48, count: 16 }
            ],
            'NCM-460': [
                { prefix: 'ge100', start: 0, count: 24 },
                { prefix: 'ge400', start: 24, count: 8 }
            ],
            'NCM-200': [
                { prefix: 'ge100', start: 0, count: 12 },
                { prefix: 'ge400', start: 12, count: 4 }
            ]
        };
    }

    // ========== PUBLIC API ==========

    /**
     * Get a platform by official name
     * @param {string} official - Platform official name (e.g., 'SA-40C')
     * @returns {object|null} Platform object or null
     */
    getPlatform(official) {
        for (const category of Object.values(this.platforms)) {
            const platform = category.platforms.find(p => p.official === official);
            if (platform) return platform;
        }
        return null;
    }

    /**
     * Get all platforms in a category
     * @param {string} categoryName - Category name (SA, CL, NC-AI, DNAAS)
     * @returns {array} Array of platform objects
     */
    getPlatformsByCategory(categoryName) {
        const category = this.platforms[categoryName];
        return category ? category.platforms : [];
    }

    /**
     * Get all categories
     * @returns {string[]} Array of category names
     */
    getCategories() {
        return Object.keys(this.platforms);
    }

    /**
     * Get transceivers for a speed
     * @param {string} speed - Speed category (1G, 10G, 100G, 400G, 800G, MGMT)
     * @returns {array} Array of transceiver objects
     */
    getTransceiversForSpeed(speed) {
        return this.transceivers[speed] || [];
    }

    /**
     * Get transceivers valid for a specific platform
     * @param {string} speed - Speed category
     * @param {string} platformOfficial - Platform official name
     * @returns {array} Filtered array of transceivers
     */
    getTransceiversForPlatform(speed, platformOfficial) {
        const speedTransceivers = this.transceivers[speed] || [];
        return speedTransceivers.filter(t => 
            t.platforms.includes('all') || t.platforms.includes(platformOfficial)
        );
    }

    /**
     * Get transceiver speed for an interface prefix
     * @param {string} interfacePrefix - Interface prefix (e.g., 'ge100')
     * @returns {string|null} Speed category or null
     */
    getSpeedForInterface(interfacePrefix) {
        return this.interfaceToTransceiverMap[interfacePrefix] || null;
    }

    /**
     * Generate interfaces for a platform
     * @param {string} platformOfficial - Platform official name
     * @returns {array} Array of interface names
     */
    generateInterfaces(platformOfficial) {
        const config = this.interfaceConfigs[platformOfficial];
        if (!config) return [];

        const interfaces = [];
        for (const spec of config) {
            for (let i = 0; i < spec.count; i++) {
                const portNum = spec.start + i;
                interfaces.push(`${spec.prefix}-0/0/${portNum}`);
            }
        }
        return interfaces;
    }

    /**
     * Get interfaces for a platform (cached)
     * @param {string} platformOfficial - Platform official name
     * @returns {array} Array of interface names
     */
    getInterfacesForPlatform(platformOfficial) {
        const platform = this.getPlatform(platformOfficial);
        if (!platform) return this.generateInterfaces(platformOfficial);
        
        // Cache interfaces if not already generated
        if (!platform.interfaces) {
            platform.interfaces = this.generateInterfaces(platformOfficial);
        }
        return platform.interfaces;
    }

    /**
     * Find platform by display name or official name
     * @param {string} name - Display name or official name
     * @returns {object|null} Platform object or null
     */
    findPlatform(name) {
        const lowerName = name.toLowerCase();
        for (const category of Object.values(this.platforms)) {
            const platform = category.platforms.find(p => 
                p.displayName.toLowerCase() === lowerName ||
                p.official.toLowerCase() === lowerName
            );
            if (platform) return platform;
        }
        return null;
    }
}

// Export for use
window.PlatformData = PlatformData;

// Factory function
window.createPlatformData = function() {
    return new PlatformData();
};

console.log('PlatformData module loaded');
