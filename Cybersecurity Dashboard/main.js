document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    const navLinks = document.querySelectorAll('nav ul li a');
    const contentSections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section
            const targetSection = document.getElementById(this.getAttribute('data-section'));
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('dark-mode');
    if (darkModeToggle) {
        // Check local storage for dark mode preference
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
        
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'true');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'false');
            }
        });
    }
    
    // Save settings
    const saveSettingsBtn = document.getElementById('save-settings');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            const settings = {
                shodanApi: document.getElementById('shodan-api').value,
                ipinfoApi: document.getElementById('ipinfo-api').value,
                hibpApi: document.getElementById('hibp-api').value,
                twilioSid: document.getElementById('twilio-sid').value,
                twilioToken: document.getElementById('twilio-token').value,
                saveLogs: document.getElementById('save-logs').checked,
                autoRefresh: document.getElementById('auto-refresh').checked,
                refreshInterval: document.getElementById('refresh-interval').value
            };
            
            localStorage.setItem('cyberToolsSettings', JSON.stringify(settings));
            
            // Show success message
            alert('Paramètres enregistrés avec succès');
        });
        
        // Load saved settings
        const savedSettings = localStorage.getItem('cyberToolsSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            document.getElementById('shodan-api').value = settings.shodanApi || '';
            document.getElementById('ipinfo-api').value = settings.ipinfoApi || '';
            document.getElementById('hibp-api').value = settings.hibpApi || '';
            document.getElementById('twilio-sid').value = settings.twilioSid || '';
            document.getElementById('twilio-token').value = settings.twilioToken || '';
            document.getElementById('save-logs').checked = settings.saveLogs || false;
            document.getElementById('auto-refresh').checked = settings.autoRefresh || false;
            document.getElementById('refresh-interval').value = settings.refreshInterval || 60;
        }
    }
    
    // Helper functions
    window.cyberTools = {
        // Get API key from settings
        getApiKey: function(name) {
            const savedSettings = localStorage.getItem('cyberToolsSettings');
            if (!savedSettings) return null;
            
            const settings = JSON.parse(savedSettings);
            return settings[name] || null;
        },
        
        // Format date for logs
        formatDate: function(date) {
            return date.toLocaleString();
        },
        
        // Escape HTML to prevent XSS
        escapeHtml: function(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        },
        
        // Show loading state in results area
        showLoading: function(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement en cours...</div>';
            }
        },
        
        // Show error message in results area
        showError: function(elementId, message) {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = `<div class="error"><i class="fas fa-exclamation-circle"></i> Erreur: ${this.escapeHtml(message)}</div>`;
            }
        },
        
        // Copy text to clipboard
        copyToClipboard: function(text) {
            navigator.clipboard.writeText(text).then(
                function() {
                    alert('Texte copié dans le presse-papier');
                },
                function(err) {
                    console.error('Impossible de copier le texte: ', err);
                }
            );
        }
    };
});