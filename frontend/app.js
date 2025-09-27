function createTable(data, columns) {
    // Create a div to hold either the table or the "no data" message
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
    
    // Add the table to the container
    container.appendChild(table);
    return container;
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

        // Define columns for the tables
        const columns = ['date', 'amount', 'vendor', 'description', 'bank_reference', 'ledger_reference'];

        // Update reconciled transactions table
        const reconciledTable = document.getElementById('reconciledTable');
        reconciledTable.innerHTML = '';
        reconciledTable.appendChild(createTable(data.reconciled, columns));

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
