function createTable(data, columns) {
    if (!data || data.length === 0) return '<p>No data available</p>';

    const table = document.createElement('table');
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column.charAt(0).toUpperCase() + column.slice(1);
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
            td.textContent = row[column] || '';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    return table;
}

function updateStatus(message, isError = false) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = 'status-section ' + (isError ? 'error' : 'success');
}

async function uploadFiles() {
    try {
        const bankFile = document.getElementById("bankFile").files[0];
        const ledgerFile = document.getElementById("ledgerFile").files[0];
        
        if (!bankFile || !ledgerFile) {
            throw new Error("Please select both bank statement and ledger files");
        }

        updateStatus("Uploading files...");
        
        const formData = new FormData();
        formData.append("bank_file", bankFile);
        formData.append("ledger_file", ledgerFile);

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

        // Define columns for the tables
        const columns = ['date', 'amount', 'vendor', 'description', 'bank_reference', 'ledger_reference'];

        // Update reconciled transactions table
        const reconciledTable = document.getElementById('reconciledTable');
        reconciledTable.innerHTML = '';
        reconciledTable.appendChild(createTable(data.reconciled, columns));

        // Update unmatched transactions tables
        const unmatchedTable = document.getElementById('unmatchedTable');
        unmatchedTable.innerHTML = `
            <h3>Unmatched Bank Transactions</h3>
            ${createTable(data.unmatched_bank, ['date', 'amount', 'vendor', 'description']).outerHTML}
            <h3>Unmatched Ledger Transactions</h3>
            ${createTable(data.unmatched_ledger, ['date', 'amount', 'vendor', 'description']).outerHTML}
        `;

    } catch (error) {
        console.error("Upload error:", error);
        updateStatus(error.message, true);
    }
}
