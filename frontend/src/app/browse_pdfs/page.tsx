"use client";

import { useState, useContext } from "react";
import axios from "axios";
import SearchBar from "@/components/ui/searchbar";
import { toast } from "sonner";
import React from "react";
import "@/app/notespage/styles.css";
import { AuthContext } from "@/app/contexts/AuthContext";
import { Trash2 } from "lucide-react"; // Assuming lucide-react is available, or use text/emoji

interface Document {
  id: string;
  topic: string;
  uploaded_by: string;
  created_at: string;
  first_page_base64?: string;
  pdf_url: string;
}

const DocumentsPage = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const { username } = useContext(AuthContext);

  // Debugging logs
  console.log("Current logged in username:", username);

  const fetchDocuments = async (query: string) => {
    if (!query.trim()) return;
    
    setLoading(true);

    try {
      const response = await axios.get(
        `http://localhost:8000/search_pdfs/?topic=${query}`
      );
      
      if (response.status === 204) {
        toast.error("No PDFs found.")
        setDocuments([]);
      } else {
        console.log(response.data.result);
        setDocuments(response.data.result);
      }
    } catch (err) {
      console.error("Error fetching documents:", err);
      toast.error("Failed to fetch documents.");
    }
    setLoading(false);
  };

  const handleDownload = (e: React.MouseEvent<HTMLAnchorElement, MouseEvent>, doc: Document) => {
    // 目前仅作为占位符以修复编译错误
    // 如果需要特定下载逻辑（如在新标签页打开或强制下载），可以在此处添加
    console.log("Opening document:", doc.topic);
  };

  const handleDelete = async (e: React.MouseEvent<HTMLButtonElement>, docId: string) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm("Are you sure you want to delete this document?")) return;

    try {
      await axios.delete(`http://localhost:8000/delete_pdf/${docId}/`);
      toast.success("Document deleted successfully");
      setDocuments(documents.filter((doc) => doc.id !== docId));
    } catch (err) {
      console.error("Error deleting document:", err);
      toast.error("Failed to delete document");
    }
  };

  return (
    <div className="min-h-screen p-6 p-6 flex flex-col items-center">
      <h1 className="text-3xl font-bold text-center mb-6">Search Documents</h1>
      <p className="text-lg text-gray-600 mb-5 text-center max-w-xl">
        Enter your query below and get the notes generated for you.
      </p>
      <div className="flex flex-col items-center mb-6">
      <div className="max-w-md mb-2">
        <SearchBar onSearch={(query) => fetchDocuments(query)} />
      </div>
  
      <div className="h-6 flex items-center justify-center">
        {loading && <div className="loader"></div>}
      </div>
</div>

      

      {/* Document List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {documents.map((doc) => {
           const isOwner = username === doc.uploaded_by;
           // console.log(`Doc: ${doc.topic}, UploadedBy: ${doc.uploaded_by}, CurrentUser: ${username}, IsOwner: ${isOwner}`);
           return (
          <div key={doc.id} className="relative group">
          <a
            href={doc.pdf_url}
            onClick={(e) => handleDownload(e, doc)}
            className="block bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300 cursor-pointer h-full"
          >
            {doc.first_page_base64 ? (
              <img
                src={`data:image/png;base64,${doc.first_page_base64}`}
                alt={doc.topic}
                className="w-full h-40 object-cover rounded-md"
              />
            ) : (
              <div className="w-full h-40 flex items-center justify-center bg-gray-200 rounded-md">
                No Preview Available
              </div>
            )}
            <h2 className="mt-2 text-lg font-semibold">{doc.topic}</h2>
            <p className="text-gray-500">By: {doc.uploaded_by}</p>
            <p className="text-gray-400 text-sm">
              Created: {new Date(doc.created_at).toLocaleDateString()}
            </p>
          </a>
          {isOwner && (
            <button
              onClick={(e) => handleDelete(e, doc.id)}
              className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 z-20"
              title="Delete Note"
            >
              <Trash2 size={16} />
            </button>
          )}
          </div>
        )})}
      </div>
    </div>
  );
};

export default DocumentsPage;
