function getConfidenceClass(score) {
    if (score >= 0.9) return 'high-confidence';
    if (score >= 0.8) return 'medium-confidence';
    return 'low-confidence';
}

function formatCurrency(amount) {
    // Check if amount is valid
    if (amount === null || amount === undefined || isNaN(amount) || amount === '') {
        return '₹0.00';
    }
    
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount)) {
        return '₹0.00';
    }
    
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(numAmount);
}

function formatDate(dateStr) {
    // Check if date string is valid
    if (!dateStr || dateStr === '' || dateStr === 'nan' || dateStr === 'null') {
        return '-';
    }
    
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        return '-';
    }
    
    return date.toLocaleDateString('en-IN');
}

function createMetricsPanel(metrics) {
    const metricsPanel = document.getElementById('metricsPanel');
    metricsPanel.innerHTML = '';

    const metricCards = [
        { label: 'Total Matches', value: metrics.total_matches },
        { label: 'High Confidence', value: metrics.high_confidence },
        { label: 'Medium Confidence', value: metrics.medium_confidence },
        { label: 'Low Confidence', value: metrics.low_confidence },
        { label: 'Average Score', value: metrics.average_score.toFixed(2) },
        { label: 'Match Rate', value: `${((metrics.total_matches / (metrics.total_matches + metrics.unmatched_total)) * 100).toFixed(1)}%` }
    ];

    metricCards.forEach(metric => {
        const card = document.createElement('div');
        card.className = 'metric-card';
        card.innerHTML = `
            <div class="metric-value">${metric.value}</div>
            <div class="metric-label">${metric.label}</div>
        `;
        metricsPanel.appendChild(card);
    });
}

function createDuplicatesPanel(duplicates) {
    const duplicatesList = document.getElementById('duplicatesList');
    duplicatesList.innerHTML = '';

    const { gstr2b, tally } = duplicates;

    if (Object.keys(gstr2b).length === 0 && Object.keys(tally).length === 0) {
        duplicatesList.innerHTML = '<p>No potential duplicates found.</p>';
        return;
    }

    if (Object.keys(gstr2b).length > 0) {
        const gstr2bSection = document.createElement('div');
        gstr2bSection.innerHTML = '<h3>GSTR2B Duplicates</h3>';
        Object.entries(gstr2b).forEach(([index, dupes]) => {
            const group = document.createElement('div');
            group.className = 'duplicate-group';
            group.innerHTML = `<p>Transaction ${index} has similar entries: ${dupes.join(', ')}</p>`;
            gstr2bSection.appendChild(group);
        });
        duplicatesList.appendChild(gstr2bSection);
    }

    if (Object.keys(tally).length > 0) {
        const tallySection = document.createElement('div');
        tallySection.innerHTML = '<h3>Tally Duplicates</h3>';
        Object.entries(tally).forEach(([index, dupes]) => {
            const group = document.createElement('div');
            group.className = 'duplicate-group';
            group.innerHTML = `<p>Transaction ${index} has similar entries: ${dupes.join(', ')}</p>`;
            tallySection.appendChild(group);
        });
        duplicatesList.appendChild(tallySection);
    }
}

function createTable(data, columns) {
    const container = document.createElement('div');
    
    if (!data || data.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No data available';
        container.appendChild(p);
        return container;
    }

    const table = document.createElement('table');
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    // Add confidence score column for reconciled transactions
    if (data[0].hasOwnProperty('match_score')) {
        columns = ['match_score', ...columns];
    }
    
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column.charAt(0).toUpperCase() + column.slice(1).replace('_', ' ');
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        columns.forEach(column => {
            const td = document.createElement('td');
            
            if (column === 'match_score') {
                const score = parseFloat(row[column] || 0);
                td.innerHTML = `<span class="match-score ${getConfidenceClass(score)}">${score.toFixed(2)}</span>`;
            } else if (column === 'amount') {
                td.textContent = formatCurrency(row[column]);
            } else if (column === 'date') {
                td.textContent = formatDate(row[column]);
            } else {
                td.textContent = row[column] || '';
            }
            
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    // Add the table to the container
    container.appendChild(table);
    return container;
}

function exportToExcel() {
    if (!window.reconciledData) {
        updateStatus('No data to export', true);
        return;
    }

    // Prepare data for export
    const workbook = XLSX.utils.book_new();
    
    // Export reconciled transactions
    if (window.reconciledData.length > 0) {
        const reconciled = XLSX.utils.json_to_sheet(window.reconciledData);
        XLSX.utils.book_append_sheet(workbook, reconciled, 'Reconciled');
    }
    
    // Export unmatched transactions if available
    if (window.unmatchedBank && window.unmatchedBank.length > 0) {
        const unmatchedBank = XLSX.utils.json_to_sheet(window.unmatchedBank);
        XLSX.utils.book_append_sheet(workbook, unmatchedBank, 'Unmatched GSTR2B');
    }
    
    if (window.unmatchedLedger && window.unmatchedLedger.length > 0) {
        const unmatchedLedger = XLSX.utils.json_to_sheet(window.unmatchedLedger);
        XLSX.utils.book_append_sheet(workbook, unmatchedLedger, 'Unmatched Tally');
    }

    // Export the workbook
    XLSX.writeFile(workbook, 'reconciliation_report.xlsx');
}

function updateStatus(message, isError = false) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = 'status-section ' + (isError ? 'error' : 'success');
}

async function uploadFiles() {
    try {
        const gstr2bFile = document.getElementById("gstr2bFile").files[0];
        const tallyFile = document.getElementById("tallyFile").files[0];
        
        if (!gstr2bFile || !tallyFile) {
            throw new Error("Please select both GSTR2B and Tally files");
        }

        updateStatus("Uploading files...");
        
        const formData = new FormData();
        formData.append("bank_file", gstr2bFile);  // Keep this name for backend compatibility
        formData.append("ledger_file", tallyFile);  // Keep this name for backend compatibility

        const response = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        updateStatus("Files processed successfully!");

        // Update metrics panel
        createMetricsPanel(data.metrics);

        // Update duplicates panel
        createDuplicatesPanel(data.duplicates);

        // Define columns for the tables
        const columns = ['date', 'amount', 'vendor', 'gstr2b_reference', 'tally_reference'];

        // Store the reconciled data globally for filtering
        window.reconciledData = data.reconciled;

        // Function to filter and display reconciled transactions
        function updateReconciledTable(confidence = 'all') {
            const filtered = window.reconciledData.filter(row => {
                const score = row.match_score;
                switch(confidence) {
                    case 'high': return score >= 0.9;
                    case 'medium': return score >= 0.8 && score < 0.9;
                    case 'low': return score < 0.8;
                    default: return true;
                }
            });
            
            const reconciledTable = document.getElementById('reconciledTable');
            reconciledTable.innerHTML = '';
            reconciledTable.appendChild(createTable(filtered, columns));
        }

        // Initial display of reconciled transactions
        updateReconciledTable();

        // Add confidence filter event listener
        document.getElementById('confidenceFilter').addEventListener('change', (e) => {
            updateReconciledTable(e.target.value);
        });

        // Update unmatched transactions tables
        const unmatchedTable = document.getElementById('unmatchedTable');
        
        // Create container for unmatched GSTR2B transactions
        const gstr2bDiv = document.createElement('div');
        const gstr2bHeader = document.createElement('h3');
        gstr2bHeader.textContent = 'Unmatched GSTR2B Transactions';
        gstr2bDiv.appendChild(gstr2bHeader);
        gstr2bDiv.appendChild(createTable(data.unmatched_bank, ['date', 'amount', 'vendor', 'reference']));

        // Create container for unmatched Tally transactions
        const tallyDiv = document.createElement('div');
        const tallyHeader = document.createElement('h3');
        tallyHeader.textContent = 'Unmatched Tally Transactions';
        tallyDiv.appendChild(tallyHeader);
        tallyDiv.appendChild(createTable(data.unmatched_ledger, ['date', 'amount', 'vendor', 'reference']));

        // Clear and update the unmatched table container
        unmatchedTable.innerHTML = '';
        unmatchedTable.appendChild(gstr2bDiv);
        unmatchedTable.appendChild(tallyDiv);

    } catch (error) {
        console.error("Upload error:", error);
        updateStatus(error.message, true);
    }
}
