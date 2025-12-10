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
        `Uploaded: document_id=${res.data.document_id}, chunks=${res.data.chunks}`
      );
      setFile(null);
    } catch (e) {
      console.error(e);
      setStatus("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>Upload Documents</h2>
      <p className="small">
        Upload PDFs or images with your org policies / SOPs / manuals. OpsCopilot will use
        them as context for answers.
      </p>

      <input
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,image/png,image/jpeg"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />

      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? "Uploading..." : "Upload"}
      </button>

      {status && <div className="status-text">{status}</div>}
    </div>
  );
}