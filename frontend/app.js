function getConfidenceClass(score) {
    if (score >= 0.95) return 'confidence-high';    // Perfect/near-perfect matches
    if (score >= 0.85) return 'confidence-medium';  // Good matches  
    return 'confidence-low';                        // Possible matches
}

function getConfidenceBadge(score) {
    const percentage = (score * 100).toFixed(1);
    const className = getConfidenceClass(score);
    return `<span class="confidence-badge ${className}">${percentage}%</span>`;
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
    
    // Show the metrics section
    document.getElementById('metricsSection').style.display = 'block';

    const metricCards = [
        { 
            label: 'Total Matches', 
            value: metrics.total_matches,
            icon: 'check-circle-2',
            type: 'success'
        },
        { 
            label: 'High Confidence', 
            value: metrics.high_confidence,
            icon: 'thumbs-up',
            type: 'success'
        },
        { 
            label: 'Medium Confidence', 
            value: metrics.medium_confidence,
            icon: 'minus-circle',
            type: 'warning'
        },
        { 
            label: 'Low Confidence', 
            value: metrics.low_confidence,
            icon: 'alert-triangle',
            type: 'error'
        },
        { 
            label: 'Average Score', 
            value: `${(metrics.average_score * 100).toFixed(1)}%`,
            icon: 'target',
            type: 'info'
        },
        { 
            label: 'Match Rate', 
            value: `${((metrics.total_matches / (metrics.total_matches + metrics.unmatched_total)) * 100).toFixed(1)}%`,
            icon: 'percent',
            type: 'info'
        }
    ];

    metricCards.forEach(metric => {
        const card = document.createElement('div');
        card.className = `metric-card ${metric.type}`;
        card.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm opacity-90">${metric.label}</p>
                    <p class="text-3xl font-bold">${metric.value}</p>
                </div>
                <div class="p-3 bg-white bg-opacity-20 rounded-lg">
                    <i data-lucide="${metric.icon}" class="w-6 h-6"></i>
                </div>
            </div>
        `;
        metricsPanel.appendChild(card);
    });
    
    // Re-initialize icons for the new cards
    lucide.createIcons();
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

function createReconciledTable(data) {
    const container = document.createElement('div');
    
    // Show the reconciled section
    document.getElementById('reconciledSection').style.display = 'block';
    
    if (!data || data.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'text-center py-12';
        emptyState.innerHTML = `
            <div class="mx-auto h-12 w-12 text-gray-400 mb-4">
                <i data-lucide="file-x" class="w-12 h-12"></i>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">No reconciled transactions</h3>
            <p class="text-gray-500">Upload files to see reconciled data here.</p>
        `;
        container.appendChild(emptyState);
        lucide.createIcons();
        return container;
    }

    const table = document.createElement('table');
    table.className = 'modern-table';
    
    // Create header with grouped columns
    const thead = document.createElement('thead');
    
    // Main header row
    const mainHeaderRow = document.createElement('tr');
    
    // Match Info columns
    const matchHeader = document.createElement('th');
    matchHeader.textContent = 'Match Info';
    matchHeader.className = 'field-header-match';
    matchHeader.colSpan = 5;
    mainHeaderRow.appendChild(matchHeader);
    
    // GSTR2B columns
    const gstr2bHeader = document.createElement('th');
    gstr2bHeader.textContent = 'GSTR2B Data';
    gstr2bHeader.className = 'field-header-gstr2b';
    gstr2bHeader.colSpan = 7;
    mainHeaderRow.appendChild(gstr2bHeader);
    
    // Tally columns
    const tallyHeader = document.createElement('th');
    tallyHeader.textContent = 'Tally Data';
    tallyHeader.className = 'field-header-tally';
    tallyHeader.colSpan = 7;
    mainHeaderRow.appendChild(tallyHeader);
    
    thead.appendChild(mainHeaderRow);
    
    // Sub header row
    const subHeaderRow = document.createElement('tr');
    
    // Match Info sub-headers
    ['Score', 'Invoice No', 'Date', 'Amount', 'Vendor'].forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        th.className = 'field-header-match';
        subHeaderRow.appendChild(th);
    });
    
    // GSTR2B sub-headers
    ['Date', 'Invoice', 'GSTIN', 'Total Amt', 'Taxable', 'IGST', 'CGST/SGST'].forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        th.className = 'field-header-gstr2b';
        subHeaderRow.appendChild(th);
    });
    
    // Tally sub-headers
    ['Date', 'Invoice', 'GSTIN', 'Total Amt', 'Base Amt', 'Tax Amt', 'Type'].forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        th.className = 'field-header-tally';
        subHeaderRow.appendChild(th);
    });
    
    thead.appendChild(subHeaderRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        // Match Info cells
        const scoreCell = document.createElement('td');
        const score = parseFloat(row.match_score || 0);
        scoreCell.innerHTML = `<span class="match-score ${getConfidenceClass(score)}">${score.toFixed(3)}</span>`;
        scoreCell.className = 'match-field';
        tr.appendChild(scoreCell);
        
        const invoiceCell = document.createElement('td');
        invoiceCell.textContent = row.invoice_no || '';
        invoiceCell.className = 'match-field';
        tr.appendChild(invoiceCell);
        
        const dateCell = document.createElement('td');
        dateCell.textContent = formatDate(row.date);
        dateCell.className = `match-field ${row.date_difference === 0 ? 'date-exact' : 'date-diff'}`;
        tr.appendChild(dateCell);
        
        const amountCell = document.createElement('td');
        amountCell.textContent = formatCurrency(row.amount);
        const amountDiff = row.amount_difference || 0;
        const amountClass = amountDiff === 0 ? 'amount-exact' : amountDiff < 1000 ? 'amount-small-diff' : 'amount-large-diff';
        amountCell.className = `match-field ${amountClass}`;
        tr.appendChild(amountCell);
        
        const vendorCell = document.createElement('td');
        vendorCell.textContent = row.vendor || '';
        vendorCell.className = 'match-field';
        tr.appendChild(vendorCell);
        
        // GSTR2B cells with error handling
        try {
            [
                formatDate(row.gstr2b_date),
                row.gstr2b_invoice_no || '',
                row.gstr2b_supplier_gstin || '',
                formatCurrency(row.gstr2b_total_amount),
                formatCurrency(row.gstr2b_taxable_value),
                formatCurrency(row.gstr2b_igst),
                formatCurrency((row.gstr2b_cgst || 0) + (row.gstr2b_sgst || 0))
            ].forEach(value => {
                const td = document.createElement('td');
                td.innerHTML = value || '';
                td.className = 'gstr2b-field';
                tr.appendChild(td);
            });
        } catch (e) {
            console.error("Error creating GSTR2B cells:", e, row);
            // Fallback: create empty cells
            for (let i = 0; i < 7; i++) {
                const td = document.createElement('td');
                td.textContent = 'Error';
                td.className = 'gstr2b-field';
                tr.appendChild(td);
            }
        }
        
        // Tally cells with error handling
        try {
            [
                formatDate(row.tally_date),
                row.tally_invoice_no || '',
                row.tally_supplier_gstin || '',
                formatCurrency(row.tally_total_amount),
                formatCurrency(row.tally_base_amount),
                formatCurrency(row.tally_tax_amount),
                row.tally_type || ''
            ].forEach(value => {
                const td = document.createElement('td');
                td.innerHTML = value || '';
                td.className = 'tally-field';
                tr.appendChild(td);
            });
        } catch (e) {
            console.error("Error creating Tally cells:", e, row);
            // Fallback: create empty cells
            for (let i = 0; i < 7; i++) {
                const td = document.createElement('td');
                td.textContent = 'Error';
                td.className = 'tally-field';
                tr.appendChild(td);
            }
        }
        
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    container.appendChild(table);
    return container;
}

function createUnmatchedTable(data, source) {
    const container = document.createElement('div');
    
    // Show the unmatched section
    document.getElementById('unmatchedSection').style.display = 'block';
    
    if (!data || data.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'text-center py-8';
        emptyState.innerHTML = `
            <div class="mx-auto h-12 w-12 text-green-400 mb-4">
                <i data-lucide="check-circle" class="w-12 h-12"></i>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">No unmatched ${source} transactions</h3>
            <p class="text-gray-500">All ${source} transactions were successfully matched!</p>
        `;
        container.appendChild(emptyState);
        lucide.createIcons();
        return container;
    }

    const table = document.createElement('table');
    table.className = 'modern-table';
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    const columns = source === 'GSTR2B' 
        ? ['date', 'invoice_no', 'supplier_gstin', 'total_amount', 'taxable_value', 'igst', 'cgst', 'sgst']
        : ['date', 'invoice_no', 'supplier_gstin', 'total_amount', 'base_amount', 'tax_amount', 'type'];
    
    const headerLabels = source === 'GSTR2B'
        ? ['Date', 'Invoice No', 'Supplier GSTIN', 'Total Amount', 'Taxable Value', 'IGST', 'CGST', 'SGST']
        : ['Date', 'Invoice No', 'Supplier GSTIN', 'Total Amount', 'Base Amount', 'Tax Amount', 'Type'];
    
    headerLabels.forEach((label, index) => {
        const th = document.createElement('th');
        th.textContent = label;
        th.className = source === 'GSTR2B' ? 'field-header-gstr2b' : 'field-header-tally';
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
            
            // Only format currency for actual amount and GST amount fields, not GSTIN
            if (column.includes('amount') || 
                (column.includes('gst') && !column.includes('gstin'))) {
                td.textContent = formatCurrency(row[column]);
            } else if (column === 'date') {
                td.textContent = formatDate(row[column]);
            } else {
                td.textContent = row[column] || '';
            }
            
            td.className = source === 'GSTR2B' ? 'gstr2b-field' : 'tally-field';
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
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
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `reconciliation_report_${timestamp}.xlsx`);
}

function exportUnmatchedGSTR2B() {
    if (!window.unmatchedBank || window.unmatchedBank.length === 0) {
        updateStatus('No unmatched GSTR2B data to export', true);
        return;
    }

    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(window.unmatchedBank);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Unmatched GSTR2B');
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `unmatched_gstr2b_${timestamp}.xlsx`);
    updateStatus('Unmatched GSTR2B data exported successfully!');
}

function exportUnmatchedTally() {
    if (!window.unmatchedLedger || window.unmatchedLedger.length === 0) {
        updateStatus('No unmatched Tally data to export', true);
        return;
    }

    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(window.unmatchedLedger);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Unmatched Tally');
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `unmatched_tally_${timestamp}.xlsx`);
    updateStatus('Unmatched Tally data exported successfully!');
}

function exportAllUnmatched() {
    if ((!window.unmatchedBank || window.unmatchedBank.length === 0) && 
        (!window.unmatchedLedger || window.unmatchedLedger.length === 0)) {
        updateStatus('No unmatched data to export', true);
        return;
    }

    const workbook = XLSX.utils.book_new();
    
    if (window.unmatchedBank && window.unmatchedBank.length > 0) {
        const gstr2bSheet = XLSX.utils.json_to_sheet(window.unmatchedBank);
        XLSX.utils.book_append_sheet(workbook, gstr2bSheet, 'Unmatched GSTR2B');
    }
    
    if (window.unmatchedLedger && window.unmatchedLedger.length > 0) {
        const tallySheet = XLSX.utils.json_to_sheet(window.unmatchedLedger);
        XLSX.utils.book_append_sheet(workbook, tallySheet, 'Unmatched Tally');
    }
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `all_unmatched_transactions_${timestamp}.xlsx`);
    updateStatus('All unmatched data exported successfully!');
}

function updateStatus(message, type = 'success') {
    const statusDiv = document.getElementById('status');
    
    let iconName, statusClass;
    switch(type) {
        case 'error':
            iconName = 'alert-circle';
            statusClass = 'status-error';
            break;
        case 'info':
            iconName = 'info';
            statusClass = 'status-info';
            break;
        default:
            iconName = 'check-circle';
            statusClass = 'status-success';
    }
    
    statusDiv.innerHTML = `
        <div class="${statusClass}">
            <i data-lucide="${iconName}" class="w-5 h-5 mr-3 flex-shrink-0"></i>
            <span>${message}</span>
        </div>
    `;
    
    lucide.createIcons();
}

async function uploadFiles() {
    try {
        const gstr2bFile = document.getElementById("gstr2bFile").files[0];
        const tallyFile = document.getElementById("tallyFile").files[0];
        
        if (!gstr2bFile || !tallyFile) {
            throw new Error("Please select both GSTR2B and Tally files");
        }

        // Show loading overlay
        document.getElementById('loadingOverlay').style.display = 'flex';
        document.getElementById('loadingMessage').textContent = 'Uploading and processing files...';
        
        // Disable the button
        const btn = document.getElementById('reconcileBtn');
        btn.disabled = true;
        btn.innerHTML = `
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Processing...</span>
        `;

        updateStatus("Processing files...", "info");
        
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
        
        // Hide loading overlay
        document.getElementById('loadingOverlay').style.display = 'none';
        
        // Reset button
        const resetBtn = document.getElementById('reconcileBtn');
        resetBtn.disabled = false;
        resetBtn.innerHTML = `
            <i data-lucide="play" class="w-4 h-4"></i>
            <span>Start Reconciliation</span>
        `;
        lucide.createIcons();
        
        updateStatus("Files processed successfully!", "success");

        // Update metrics panel
        createMetricsPanel(data.metrics);

        // Update duplicates panel
        createDuplicatesPanel(data.duplicates);

        // Store the data globally for filtering and export
        window.reconciledData = data.reconciled || [];
        window.unmatchedBank = data.unmatched_bank || [];
        window.unmatchedLedger = data.unmatched_ledger || [];

        // Function to filter and display reconciled transactions with error handling
        function updateReconciledTable(confidence = 'all') {
            try {
                const filtered = (window.reconciledData || []).filter(row => {
                    const score = parseFloat(row.match_score) || 0;
                    switch(confidence) {
                        case 'high': return score >= 0.95;   // Perfect/near-perfect matches
                        case 'medium': return score >= 0.85 && score < 0.95;  // Good matches
                        case 'low': return score < 0.85;     // Possible matches
                        default: return true;
                    }
                });
                
                const reconciledTable = document.getElementById('reconciledTable');
                if (reconciledTable) {
                    reconciledTable.innerHTML = '';
                    if (filtered && filtered.length > 0) {
                        console.log("Creating enhanced reconciled table with", filtered.length, "transactions");
                        console.log("Sample data:", filtered[0]);
                        try {
                            reconciledTable.appendChild(createReconciledTable(filtered));
                        } catch (tableError) {
                            console.error("Error creating enhanced table, falling back:", tableError);
                            // Fallback to simple table
                            reconciledTable.innerHTML = `<p>Error creating enhanced table: ${tableError.message}</p>`;
                        }
                    } else {
                        reconciledTable.innerHTML = '<p>No reconciled transactions to display.</p>';
                    }
                }
            } catch (error) {
                console.error("Error updating reconciled table:", error);
                const reconciledTable = document.getElementById('reconciledTable');
                if (reconciledTable) {
                    reconciledTable.innerHTML = '<p>Error displaying reconciled transactions.</p>';
                }
            }
        }

        // Initial display of reconciled transactions
        console.log("Calling updateReconciledTable with data:", window.reconciledData);
        updateReconciledTable();

        // Add confidence filter event listener if not already added
        const confidenceFilter = document.getElementById('confidenceFilter');
        const existingHandler = confidenceFilter.getAttribute('data-handler-added');
        if (!existingHandler) {
            confidenceFilter.addEventListener('change', (e) => {
                updateReconciledTable(e.target.value);
            });
            confidenceFilter.setAttribute('data-handler-added', 'true');
        }

        // Update unmatched transactions tables with error handling
        try {
            const unmatchedTable = document.getElementById('unmatchedTable');
            if (unmatchedTable) {
                unmatchedTable.innerHTML = '';
                
                // Create container for unmatched GSTR2B transactions
                if (data.unmatched_bank && data.unmatched_bank.length > 0) {
                    const gstr2bDiv = document.createElement('div');
                    const gstr2bHeader = document.createElement('h3');
                    gstr2bHeader.textContent = 'Unmatched GSTR2B Transactions ';
                    gstr2bHeader.innerHTML += '<span class="source-gstr2b">GSTR2B</span>';
                    gstr2bDiv.appendChild(gstr2bHeader);
                    gstr2bDiv.appendChild(createUnmatchedTable(data.unmatched_bank, 'GSTR2B'));
                    unmatchedTable.appendChild(gstr2bDiv);
                }

                // Create container for unmatched Tally transactions
                if (data.unmatched_ledger && data.unmatched_ledger.length > 0) {
                    const tallyDiv = document.createElement('div');
                    const tallyHeader = document.createElement('h3');
                    tallyHeader.textContent = 'Unmatched Tally Transactions ';
                    tallyHeader.innerHTML += '<span class="source-tally">TALLY</span>';
                    tallyDiv.appendChild(tallyHeader);
                    tallyDiv.appendChild(createUnmatchedTable(data.unmatched_ledger, 'Tally'));
                    unmatchedTable.appendChild(tallyDiv);
                }
                
                if ((!data.unmatched_bank || data.unmatched_bank.length === 0) && 
                    (!data.unmatched_ledger || data.unmatched_ledger.length === 0)) {
                    unmatchedTable.innerHTML = '<p>No unmatched transactions found! All transactions were successfully reconciled.</p>';
                }
            }
        } catch (error) {
            console.error("Error updating unmatched tables:", error);
            const unmatchedTable = document.getElementById('unmatchedTable');
            if (unmatchedTable) {
                unmatchedTable.innerHTML = '<p>Error displaying unmatched transactions.</p>';
            }
        }

    } catch (error) {
        console.error("Upload error:", error);
        
        // Hide loading overlay
        document.getElementById('loadingOverlay').style.display = 'none';
        
        // Reset button
        const errorBtn = document.getElementById('reconcileBtn');
        errorBtn.disabled = false;
        errorBtn.innerHTML = `
            <i data-lucide="play" class="w-4 h-4"></i>
            <span>Start Reconciliation</span>
        `;
        lucide.createIcons();
        
        updateStatus(error.message, "error");
    }
}
