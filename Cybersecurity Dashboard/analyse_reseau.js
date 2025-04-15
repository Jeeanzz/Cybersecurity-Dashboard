document.addEventListener('DOMContentLoaded', function() {
    // IP Info Tool
    const analyzeIpBtn = document.getElementById('analyze-ip');
    if (analyzeIpBtn) {
        analyzeIpBtn.addEventListener('click', function() {
            const ipAddress = document.getElementById('ip-address').value.trim();
            if (!ipAddress) {
                cyberTools.showError('ip-results', 'Veuillez entrer une adresse IP ou un nom de domaine');
                return;
            }
            
            cyberTools.showLoading('ip-results');
            
            // IP info API call
            const ipInfoKey = cyberTools.getApiKey('ipinfoApi');
            const apiUrl = `https://ipinfo.io/${ipAddress}/json${ipInfoKey ? `?token=${ipInfoKey}` : ''}`;
            
            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Erreur lors de la requête IP Info');
                    }
                    return response.json();
                })
                .then(data => {
                    const resultsArea = document.getElementById('ip-results');
                    
                    let html = `
                        <div class="result-card">
                            <h4>Informations sur ${data.ip}</h4>
                            <table class="info-table">
                                <tr>
                                    <td><strong>IP</strong></td>
                                    <td>${data.ip}</td>
                                </tr>
                    `;
                    
                    if (data.hostname) {
                        html += `
                            <tr>
                                <td><strong>Hostname</strong></td>
                                <td>${data.hostname}</td>
                            </tr>
                        `;
                    }
                    
                    if (data.city || data.region || data.country) {
                        html += `
                            <tr>
                                <td><strong>Localisation</strong></td>
                                <td>${[data.city, data.region, data.country].filter(Boolean).join(', ')}</td>
                            </tr>
                        `;
                    }
                    
                    if (data.loc) {
                        html += `
                            <tr>
                                <td><strong>Coordonnées</strong></td>
                                <td>${data.loc}</td>
                            </tr>
                        `;
                    }
                    
                    if (data.org) {
                        html += `
                            <tr>
                                <td><strong>Organisation</strong></td>
                                <td>${data.org}</td>
                            </tr>
                        `;
                    }
                    
                    if (data.postal) {
                        html += `
                            <tr>
                                <td><strong>Code Postal</strong></td>
                                <td>${data.postal}</td>
                            </tr>
                        `;
                    }
                    
                    if (data.timezone) {
                        html += `
                            <tr>
                                <td><strong>Fuseau Horaire</strong></td>
                                <td>${data.timezone}</td>
                            </tr>
                        `;
                    }
                    
                    html += `
                            </table>
                            <div class="actions">
                                <button class="btn secondary copy-btn" data-copy="${data.ip}">
                                    <i class="fas fa-copy"></i> Copier l'IP
                                </button>
                            </div>
                        </div>
                    `;
                    
                    resultsArea.innerHTML = html;
                    
                    // Add event listener for copy button
                    const copyBtn = resultsArea.querySelector('.copy-btn');
                    if (copyBtn) {
                        copyBtn.addEventListener('click', function() {
                            const textToCopy = this.getAttribute('data-copy');
                            cyberTools.copyToClipboard(textToCopy);
                        });
                    }
                })
                .catch(error => {
                    cyberTools.showError('ip-results', error.message);
                });
        });
    }
    
    // Port Scan Tool
    const portScanBtn = document.getElementById('start-scan');
    if (portScanBtn) {
        portScanBtn.addEventListener('click', function() {
            const ipAddress = document.getElementById('scan-ip').value.trim();
            const portRange = document.getElementById('port-range').value.trim();
            
            if (!ipAddress) {
                cyberTools.showError('scan-results', 'Veuillez entrer une adresse IP');
                return;
            }
            
            if (!portRange) {
                cyberTools.showError('scan-results', 'Veuillez spécifier les ports à scanner');
                return;
            }
            
            cyberTools.showLoading('scan-results');
            
            // Call backend API for port scanning
            fetch('/api/scan-ports', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: ipAddress,
                    ports: portRange
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur lors du scan de ports');
                }
                return response.json();
            })
            .then(data => {
                const resultsArea = document.getElementById('scan-results');
                
                let html = `
                    <div class="result-card">
                        <h4>Résultats du scan pour ${ipAddress}</h4>
                        <p>Ports scannés: ${portRange}</p>
                        <table class="info-table">
                            <thead>
                                <tr>
                                    <th>Port</th>
                                    <th>État</th>
                                    <th>Service</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                if (data.ports && data.ports.length > 0) {
                    data.ports.forEach(port => {
                        html += `
                            <tr>
                                <td>${port.number}</td>
                                <td>
                                    <span class="status-badge ${port.open ? 'open' : 'closed'}">
                                        ${port.open ? 'Ouvert' : 'Fermé'}
                                    </span>
                                </td>
                                <td>${port.service || '-'}</td>
                            </tr>
                        `;
                    });
                } else {
                    html += `
                        <tr>
                            <td colspan="3" class="empty-state">Aucun port ouvert trouvé</td>
                        </tr>
                    `;
                }
                
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                resultsArea.innerHTML = html;
            })
            .catch(error => {
                // Fallback for development/demo
                if (error.message.includes('Failed to fetch') || error.message.includes('scan-ports')) {
                    const resultsArea = document.getElementById('scan-results');
                    
                    let html = `
                        <div class="result-card">
                            <h4>Résultats du scan pour ${ipAddress} (DÉMO)</h4>
                            <p class="note">Note: Ceci est une démonstration, le backend n'est pas connecté</p>
                            <p>Ports scannés: ${portRange}</p>
                            <table class="info-table">
                                <thead>
                                    <tr>
                                        <th>Port</th>
                                        <th>État</th>
                                        <th>Service</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>22</td>
                                        <td><span class="status-badge open">Ouvert</span></td>
                                        <td>SSH</td>
                                    </tr>
                                    <tr>
                                        <td>80</td>
                                        <td><span class="status-badge open">Ouvert</span></td>
                                        <td>HTTP</td>
                                    </tr>
                                    <tr>
                                        <td>443</td>
                                        <td><span class="status-badge open">Ouvert</span></td>
                                        <td>HTTPS</td>
                                    </tr>
                                    <tr>
                                        <td>3389</td>
                                        <td><span class="status-badge closed">Fermé</span></td>
                                        <td>RDP</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    `;
                    
                    resultsArea.innerHTML = html;
                } else {
                    cyberTools.showError('scan-results', error.message);
                }
            });
        });
    }
    
    // DNS Resolution Tool
    const resolveDnsBtn = document.getElementById('resolve-dns');
    if (resolveDnsBtn) {
        resolveDnsBtn.addEventListener('click', function() {
            const domainName = document.getElementById('domain-name').value.trim();
            
            if (!domainName) {
                cyberTools.showError('dns-results', 'Veuillez entrer un nom de domaine');
                return;
            }
            
            cyberTools.showLoading('dns-results');
            
            // Call backend API for DNS resolution
            fetch('/api/resolve-dns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    domain: domainName
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur lors de la résolution DNS');
                }
                return response.json();
            })
            .then(data => {
                renderDnsResults(domainName, data);
            })
            .catch(error => {
                // Fallback for development/demo
                if (error.message.includes('Failed to fetch') || error.message.includes('resolve-dns')) {
                    const demoData = {
                        a: ['192.168.1.1', '192.168.1.2'],
                        aaaa: ['2001:0db8:85a3:0000:0000:8a2e:0370:7334'],
                        mx: ['mail.example.com', 'backup-mail.example.com'],
                        ns: ['ns1.example.com', 'ns2.example.com'],
                        txt: ['v=spf1 include:_spf.example.com ~all']
                    };
                    renderDnsResults(domainName, demoData, true);
                } else {
                    cyberTools.showError('dns-results', error.message);
                }
            });
            
            function renderDnsResults(domain, data, isDemo = false) {
                const resultsArea = document.getElementById('dns-results');
                
                let html = `
                    <div class="result-card">
                        <h4>Résolution DNS pour ${domain}</h4>
                        ${isDemo ? '<p class="note">Note: Ceci est une démonstration, le backend n\'est pas connecté</p>' : ''}
                        <div class="dns-records">
                `;
                
                // A Records
                if (data.a && data.a.length > 0) {
                    html += `
                        <div class="record-group">
                            <h5>Enregistrements A</h5>
                            <ul>
                    `;
                    
                    data.a.forEach(record => {
                        html += `<li>${record}</li>`;
                    });
                    
                    html += `
                            </ul>
                        </div>
                    `;
                }
                
                // AAAA Records
                if (data.aaaa && data.aaaa.length > 0) {
                    html += `
                        <div class="record-group">
                            <h5>Enregistrements AAAA (IPv6)</h5>
                            <ul>
                    `;
                    
                    data.aaaa.forEach(record => {
                        html += `<li>${record}</li>`;
                    });
                    
                    html += `
                            </ul>
                        </div>
                    `;
                }
                
                // MX Records
                if (data.mx && data.mx.length > 0) {
                    html += `
                        <div class="record-group">
                            <h5>Enregistrements MX</h5>
                            <ul>
                    `;
                    
                    data.mx.forEach(record => {
                        html += `<li>${record}</li>`;
                    });
                    
                    html += `
                            </ul>
                        </div>
                    `;
                }
                
                // NS Records
                if (data.ns && data.ns.length > 0) {
                    html += `
                        <div class="record-group">
                            <h5>Serveurs de noms (NS)</h5>
                            <ul>
                    `;
                    
                    data.ns.forEach(record => {
                        html += `<li>${record}</li>`;
                    });
                    
                    html += `
                            </ul>
                        </div>
                    `;
                }
                
                // TXT Records
                if (data.txt && data.txt.length > 0) {
                    html += `
                        <div class="record-group">
                            <h5>Enregistrements TXT</h5>
                            <ul>
                    `;
                    
                    data.txt.forEach(record => {
                        html += `<li>${cyberTools.escapeHtml(record)}</li>`;
                    });
                    
                    html += `
                            </ul>
                        </div>
                    `;
                }
                
                html += `
                        </div>
                    </div>
                `;
                
                resultsArea.innerHTML = html;
            }
        });
    }
    
    // Network Scan Tool
    const scanNetworkBtn = document.getElementById('scan-network');
    if (scanNetworkBtn) {
        scanNetworkBtn.addEventListener('click', function() {
            const networkRange = document.getElementById('network-range').value.trim();
            
            if (!networkRange) {
                cyberTools.showError('network-results', 'Veuillez entrer une plage réseau');
                return;
            }
            
            cyberTools.showLoading('network-results');
            
            // Call backend API for network scanning
            fetch('/api/scan-network', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    range: networkRange
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur lors du scan réseau');
                }
                return response.json();
            })
            .then(data => {
                renderNetworkResults(networkRange, data);
            })
            .catch(error => {
                // Fallback for development/demo
                if (error.message.includes('Failed to fetch') || error.message.includes('scan-network')) {
                    const demoData = {
                        devices: [
                            { ip: '192.168.1.1', mac: '00:1A:2B:3C:4D:5E', hostname: 'router.local', vendor: 'Cisco Systems' },
                            { ip: '192.168.1.2', mac: '11:22:33:44:55:66', hostname: 'desktop-pc.local', vendor: 'Dell Inc.' },
                            { ip: '192.168.1.3', mac: 'AA:BB:CC:DD:EE:FF', hostname: 'laptop.local', vendor: 'Apple Inc.' },
                            { ip: '192.168.1.4', mac: '12:34:56:78:90:AB', hostname: 'smartphone.local', vendor: 'Samsung Electronics' }
                        ]
                    };
                    renderNetworkResults(networkRange, demoData, true);
                } else {
                    cyberTools.showError('network-results', error.message);
                }
            });
            
            function renderNetworkResults(range, data, isDemo = false) {
                const resultsArea = document.getElementById('network-results');
                
                let html = `
                    <div class="result-card">
                        <h4>Scan réseau pour ${range}</h4>
                        ${isDemo ? '<p class="note">Note: Ceci est une démonstration, le backend n\'est pas connecté</p>' : ''}
                        <p>Appareils découverts: ${data.devices.length}</p>
                        <table class="info-table">
                            <thead>
                                <tr>
                                    <th>IP</th>
                                    <th>MAC</th>
                                    <th>Hostname</th>
                                    <th>Fabricant</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                if (data.devices && data.devices.length > 0) {
                    data.devices.forEach(device => {
                        html += `
                            <tr>
                                <td>${device.ip}</td>
                                <td>${device.mac || '-'}</td>
                                <td>${device.hostname || '-'}</td>
                                <td>${device.vendor || '-'}</td>
                            </tr>
                        `;
                    });
                } else {
                    html += `
                        <tr>
                            <td colspan="4" class="empty-state">Aucun appareil découvert</td>
                        </tr>
                    `;
                }
                
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                resultsArea.innerHTML = html;
            }
        });
    }
    
    // Reverse IP Tool
    const reverseLookupBtn = document.getElementById('reverse-lookup');
    if (reverseLookupBtn) {
        reverseLookupBtn.addEventListener('click', function() {
            const ipAddress = document.getElementById('reverse-ip-input').value.trim();
            
            if (!ipAddress) {
                cyberTools.showError('reverse-results', 'Veuillez entrer une adresse IP');
                return;
            }
            
            cyberTools.showLoading('reverse-results');
            
            // Call backend API for reverse IP lookup
            fetch('/api/reverse-ip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: ipAddress
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur lors de la recherche Reverse IP');
                }
                return response.json();
            })
            .then(data => {
                renderReverseResults(ipAddress, data);
            })
            .catch(error => {
                // Fallback for development/demo
                if (error.message.includes('Failed to fetch') || error.message.includes('reverse-ip')) {
                    const demoData = {
                        domains: [
                            'example.com',
                            'blog.example.com',
                            'store.example.com',
                            'api.example.com'
                        ]
                    };
                    renderReverseResults(ipAddress, demoData, true);
                } else {
                    cyberTools.showError('reverse-results', error.message);
                }
            });
            
            function renderReverseResults(ip, data, isDemo = false) {
                const resultsArea = document.getElementById('reverse-results');
                
                let html = `
                    <div class="result-card">
                        <h4>Reverse IP pour ${ip}</h4>
                        ${isDemo ? '<p class="note">Note: Ceci est une démonstration, le backend n\'est pas connecté</p>' : ''}
                        <p>Domaines trouvés: ${data.domains.length}</p>
                `;
                
                if (data.domains && data.domains.length > 0) {
                    html += `
                        <div class="domains-list">
                            <ul>
                    `;
                    
                    data.domains.forEach(domain => {
                        html += `
                            <li>
                                <span class="domain-name">${domain}</span>
                                <button class="btn small copy-btn" data-copy="${domain}">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </li>
                        `;
                    });
                    
                    html += `
                            </ul>
                        </div>
                    `;
                } else {
                    html += `
                        <p class="empty-state">Aucun domaine trouvé pour cette adresse IP</p>
                    `;
                }
                
                html += `
                    </div>
                `;
                
                resultsArea.innerHTML = html;
                
                // Add event listeners for copy buttons
                const copyBtns = resultsArea.querySelectorAll('.copy-btn');
                copyBtns.forEach(btn => {
                    btn.addEventListener('click', function() {
                        const textToCopy = this.getAttribute('data-copy');
                        cyberTools.copyToClipboard(textToCopy);
                    });
                });
            }
        });
    }
});