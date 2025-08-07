document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const resultsSection = document.getElementById('results-section');
    const loadingIndicator = document.getElementById('loading');
    const chainsContainer = document.getElementById('chains-container');
    const rackNameElement = document.getElementById('rack-name');
    const rackStatsElement = document.getElementById('rack-stats');

    // Handle file browsing
    dropZone.addEventListener('click', () => fileInput.click());

    // Handle file drop
    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('dragover');

        const files = event.dataTransfer.files;
        if (files.length) analyzeFiles(files);
    });

    // Handle file input changes
    fileInput.addEventListener('change', (event) => {
        const files = event.target.files;
        if (files.length) analyzeFiles(files);
    });

    // Analyze files
    function analyzeFiles(files) {
        // Backend expects single file upload
        if (files.length === 0) return;
        
        const formData = new FormData();
        formData.append('file', files[0]); // Send only the first file as 'file'

        loadingIndicator.classList.remove('hidden');
        resultsSection.classList.add('hidden');

        fetch('/api/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
                loadingIndicator.classList.add('hidden');
            } else if (data.analysis) {
                displayResults(data.analysis); // Use the analysis object from response
                loadingIndicator.classList.add('hidden');
                resultsSection.classList.remove('hidden');
            } else {
                alert('Invalid response from server');
                loadingIndicator.classList.add('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to analyze file. Is the backend running?');
            loadingIndicator.classList.add('hidden');
        });
    }

    // Display results
    function displayResults(data) {
        rackNameElement.textContent = data.rack_name || 'Unknown Rack';

        // Handle macros
        const macroControls = document.getElementById('macro-controls');
        const macroList = document.getElementById('macro-list');
        
        if (data.macro_controls && data.macro_controls.length > 0) {
            macroControls.classList.remove('hidden');
            macroList.innerHTML = data.macro_controls.map(macro => `
                <div class="macro-item">
                    <span>${macro.name}</span>
                </div>
            `).join('');
        } else {
            macroControls.classList.add('hidden');
        }

        // Set rack stats
        const totalDevices = countAllDevices(data.chains);
        rackStatsElement.innerHTML = `
            <span>Chains: ${data.chains.length}</span>
            <span>Devices: ${totalDevices}</span>
        `;

        // Display chains and devices
        chainsContainer.innerHTML = '';
        data.chains.forEach(chain => {
            const chainDiv = createChainElement(chain);
            chainsContainer.appendChild(chainDiv);
        });
    }

    // Create chain element
    function createChainElement(chain) {
        const chainDiv = document.createElement('div');
        chainDiv.className = 'chain';
        
        const chainHeader = document.createElement('div');
        chainHeader.className = 'chain-header';
        chainHeader.textContent = chain.name;
        chainDiv.appendChild(chainHeader);
        
        const devicesDiv = document.createElement('div');
        devicesDiv.className = 'devices';
        
        chain.devices.forEach(device => {
            const deviceDiv = createDeviceElement(device);
            devicesDiv.appendChild(deviceDiv);
        });
        
        chainDiv.appendChild(devicesDiv);
        return chainDiv;
    }

    // Create device element
    function createDeviceElement(device) {
        const deviceDiv = document.createElement('div');
        deviceDiv.className = 'device' + (!device.is_on ? ' off' : '');
        
        const deviceName = document.createElement('div');
        deviceName.className = 'device-name';
        deviceName.textContent = device.name;
        deviceDiv.appendChild(deviceName);
        
        // Show preset name if available
        if (device.preset_name) {
            const presetName = document.createElement('div');
            presetName.className = 'device-type';
            presetName.textContent = `Preset: ${device.preset_name}`;
            deviceDiv.appendChild(presetName);
        }
        
        // Handle nested racks
        if (device.chains && device.chains.length > 0) {
            const nestedRack = document.createElement('div');
            nestedRack.className = 'nested-rack';
            device.chains.forEach(nestedChain => {
                const nestedChainDiv = createChainElement(nestedChain);
                nestedRack.appendChild(nestedChainDiv);
            });
            deviceDiv.appendChild(nestedRack);
        }
        
        return deviceDiv;
    }

    // Count all devices including nested
    function countAllDevices(chains) {
        let count = 0;
        chains.forEach(chain => {
            chain.devices.forEach(device => {
                count++;
                if (device.chains) {
                    count += countAllDevices(device.chains);
                }
            });
        });
        return count;
    }

    // Handle "Analyze Another" button
    document.getElementById('analyze-another').addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        fileInput.value = '';
    });

    // Handle "Export JSON" button
    document.getElementById('export-json').addEventListener('click', () => {
        const data = {
            rack_name: rackNameElement.textContent,
            // You'd need to store the full data for export
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'rack-analysis.json';
        a.click();
    });
});
