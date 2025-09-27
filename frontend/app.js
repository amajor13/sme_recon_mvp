async function uploadFile() {
    try {
        const input = document.getElementById("fileInput");
        const file = input.files[0];
        
        if (!file) {
            throw new Error("Please select a file first");
        }

        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        document.getElementById("output").textContent = JSON.stringify(data, null, 2);
        document.getElementById("error").textContent = ""; // Clear any previous errors
    } catch (error) {
        console.error("Upload error:", error);
        document.getElementById("error").textContent = error.message;
    }
}
