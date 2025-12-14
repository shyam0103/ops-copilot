// src/components/DocumentUploader.jsx
import { useState } from "react";
import api from "../api";

export default function DocumentUploader() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setStatus("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setStatus(
        `✅ Uploaded: ${res.data.file_type.toUpperCase()} | Document ID: ${res.data.document_id} | Chunks: ${res.data.chunks}`
      );
      setFile(null);
      
      // Clear file input
      document.querySelector('input[type="file"]').value = '';
    } catch (e) {
      console.error(e);
      const errorMsg = e.response?.data?.detail || "Upload failed";
      setStatus(`❌ ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>📤 Upload Documents</h2>
      <p className="small">
        Upload documents with your policies, SOPs, or manuals. Supported formats:
        <br />
        <strong>PDF, DOCX, XLSX, XLS, CSV, TXT, PNG, JPG, JPEG</strong>
      </p>

      <input
        type="file"
        accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.png,.jpg,.jpeg"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />

      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? "⏳ Uploading..." : "📤 Upload"}
      </button>

      {status && (
        <div className={status.startsWith("✅") ? "status-success" : "status-error"}>
          {status}
        </div>
      )}
    </div>
  );
}