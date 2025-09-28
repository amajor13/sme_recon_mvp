// Simple debug version with error handling
function formatCurrency(amount) {
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
    if (!dateStr || dateStr === '' || dateStr === 'nan' || dateStr === 'null') {
        return '-';
    }
    
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        return '-';
    }
    
    return date.toLocaleDateString('en-IN');
}

function getConfidenceClass(score) {
    if (score >= 0.95) return 'high-confidence';
    if (score >= 0.85) return 'medium-confidence';
    return 'low-confidence';
}

function updateStatus(message, isError = false) {
    const statusDiv = document.getElementById('status');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = 'status-section ' + (isError ? 'error' : 'success');
    }
}

function createSimpleTable(data, title) {
    const container = document.createElement('div');
    const header = document.createElement('h3');
    header.textContent = title;
    container.appendChild(header);
    
    if (!data || data.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No data available';
        container.appendChild(p);
        return container;
    }

    const table = document.createElement('table');
    
    // Get all unique keys from the data
    const keys = [...new Set(data.flatMap(Object.keys))];
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    keys.forEach(key => {
        const th = document.createElement('th');
        th.textContent = key.replace(/_/g, ' ').toUpperCase();
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');
    data.forEach(row => {
        const tr = document.createElement('tr');
        keys.forEach(key => {
            const td = document.createElement('td');
            const value = row[key];
            
            if (key.includes('amount') || key.includes('gst')) {
                td.textContent = formatCurrency(value);
            } else if (key.includes('date')) {
                td.textContent = formatDate(value);
            } else if (key === 'match_score') {
                const score = parseFloat(value || 0);
                td.innerHTML = `<span class="match-score ${getConfidenceClass(score)}">${score.toFixed(3)}</span>`;
            } else {
                td.textContent = value || '';
            }
            
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    container.appendChild(table);
    return container;
}

async function uploadFiles() {
    console.log("Upload function called");
    
    try {
        const gstr2bFile = document.getElementById("gstr2bFile").files[0];
        const tallyFile = document.getElementById("tallyFile").files[0];
        
        if (!gstr2bFile || !tallyFile) {
            throw new Error("Please select both GSTR2B and Tally files");
        }

        updateStatus("Uploading files...");
        
        const formData = new FormData();
        formData.append("bank_file", gstr2bFile);
        formData.append("ledger_file", tallyFile);

        const response = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        console.log("Received data:", data);
        updateStatus("Files processed successfully!");

        // Display results simply
        const reconciledTable = document.getElementById('reconciledTable');
        if (reconciledTable) {
            reconciledTable.innerHTML = '';
            if (data.reconciled && data.reconciled.length > 0) {
                reconciledTable.appendChild(createSimpleTable(data.reconciled, 'Reconciled Transactions'));
            }
        }

        const unmatchedTable = document.getElementById('unmatchedTable');
        if (unmatchedTable) {
            unmatchedTable.innerHTML = '';
            if (data.unmatched_bank && data.unmatched_bank.length > 0) {
                unmatchedTable.appendChild(createSimpleTable(data.unmatched_bank, 'Unmatched GSTR2B'));
            }
            if (data.unmatched_ledger && data.unmatched_ledger.length > 0) {
                unmatchedTable.appendChild(createSimpleTable(data.unmatched_ledger, 'Unmatched Tally'));
            }
        }

        // Store data for export
        window.reconciledData = data.reconciled;
        window.unmatchedBank = data.unmatched_bank;
        window.unmatchedLedger = data.unmatched_ledger;

    } catch (error) {
        console.error("Upload error:", error);
        updateStatus(error.message, true);
    }
}

// Simple export functions
function exportToExcel() {
    if (!window.reconciledData) {
        updateStatus('No data to export', true);
        return;
    }

    const workbook = XLSX.utils.book_new();
    
    if (window.reconciledData.length > 0) {
        const reconciled = XLSX.utils.json_to_sheet(window.reconciledData);
        XLSX.utils.book_append_sheet(workbook, reconciled, 'Reconciled');
    }
    
    if (window.unmatchedBank && window.unmatchedBank.length > 0) {
        const unmatchedBank = XLSX.utils.json_to_sheet(window.unmatchedBank);
        XLSX.utils.book_append_sheet(workbook, unmatchedBank, 'Unmatched GSTR2B');
    }
    
    if (window.unmatchedLedger && window.unmatchedLedger.length > 0) {
        const unmatchedLedger = XLSX.utils.json_to_sheet(window.unmatchedLedger);
        XLSX.utils.book_append_sheet(workbook, unmatchedLedger, 'Unmatched Tally');
    }

    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `reconciliation_report_${timestamp}.xlsx`);
    updateStatus('Report exported successfully!');
}

console.log("Debug app.js loaded");