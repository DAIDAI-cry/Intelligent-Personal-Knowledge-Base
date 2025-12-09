"use client";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { useContext, useState, useEffect } from "react";
import { AuthContext } from "./contexts/AuthContext";
import { FileUpload } from "@/components/ui/file-upload";
import axios from "axios";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { AuthModal } from "@/components/AuthModal";

export default function Page() {
  const { isLoggedIn } = useContext(AuthContext);
  const destination = isLoggedIn ? "/notespage" : "/login";
  const destination2 = isLoggedIn ? "/browse_pdfs" : "/login";

  // Intro State
  const [showIntro, setShowIntro] = useState(true);
  const [progress, setProgress] = useState(0);
  const [showEnter, setShowEnter] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          setShowEnter(true);
          return 100;
        }
        // Randomize increment for more realistic feel
        const increment = Math.random() * 5 + 1; 
        return Math.min(prev + increment, 100);
      });
    }, 50);

    return () => clearInterval(timer);
  }, []);

  const handleEnter = () => {
    setShowLoginModal(true);
  };

  const handleAuthSuccess = () => {
    setShowLoginModal(false);
    setShowIntro(false);
  };

  const handleUpload = async (data:FormData) => {
    try {
      const token = localStorage.getItem("accessToken");
      const response = await axios.post(`http://127.0.0.1:8000/add_pdf/`, data, {
        headers: {
          "Content-Type": "multipart/form-data",
          "Authorization": `Bearer ${token}`,
        },
        withCredentials: true
      });
      if (response.status === 201) {
        toast.success("File uploaded successfully");
      }
    } catch (error) {
      toast.error("Error uploading file");
    }
  }

  if (showIntro) {
     return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-end pb-[190px] bg-black text-white overflow-hidden font-sans">
            {/* Background */}
            <div className="absolute inset-0 z-0">
                <video 
                    autoPlay 
                    loop 
                    muted 
                    playsInline
                    className={`w-full h-full object-cover transition-transform duration-[20s] ease-linear ${showEnter ? 'scale-110' : 'scale-100'}`}
                >
                    <source src="/images/kv-video.mp4" type="video/mp4" />
                </video>
                <div className="absolute inset-0 bg-black/30" />
            </div>

            {/* Content */}
            <div className="z-10 flex flex-col items-center w-full max-w-2xl px-4">
                {!showEnter ? (
                    <div className="w-full flex flex-col items-center space-y-6">
                        <Image
                            src="/images/jcczz.png"
                            alt="金铲铲之战"
                            width={500}
                            height={150}
                            className="drop-shadow-lg"
                        />
                        <div className="w-full max-w-md h-2 bg-gray-800/80 rounded-full overflow-hidden border border-blue-600/30 backdrop-blur-sm">
                            <motion.div 
                                className="h-full bg-gradient-to-r from-blue-600 via-blue-400 to-blue-200"
                                initial={{ width: "0%" }}
                                animate={{ width: `${progress}%` }}
                            />
                        </div>
                        <p className="text-blue-100/80 font-mono text-sm tracking-widest">
                            LOADING RESOURCES... {Math.floor(progress)}%
                        </p>
                    </div>
                ) : (
                    !showLoginModal && (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="flex flex-col items-center"
                        >
                            <Image 
                                src="/images/aag.png" 
                                alt="铲铲宝典" 
                                width={400} 
                                height={133}
                                className="mb-4 drop-shadow-[0_5px_5px_rgba(0,0,0,0.8)] cursor-pointer hover:scale-105 transition-transform duration-300"
                                onClick={handleEnter}
                            />
                        </motion.div>
                    )
                )}
            </div>
            <AuthModal 
                isOpen={showLoginModal} 
                onClose={() => setShowLoginModal(false)} 
                onSuccess={handleAuthSuccess} 
            />
        </div>
     )
  }

  return (
      <div className="min-h-screen w-full bg-background">
      </div>
  );
}