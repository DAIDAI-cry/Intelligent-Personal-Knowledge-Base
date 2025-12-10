"use client";
import React, { useState, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { toast } from "sonner";
import { AuthContext } from "@/app/contexts/AuthContext";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const { setIsLoggedIn } = useContext(AuthContext);
  
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    confirmPassword: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { username, password, confirmPassword } = formData;

    if (!username || !password) {
      toast.error("所有字段都是必填的。");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      toast.error("两次输入的密码不一致。");
      return;
    }

    try {
      const endpoint = isLogin ? "login/" : "signup/";
      const payload = isLogin 
        ? { username, password }
        : { username, password, confirm_password: confirmPassword };

      const response = await axios.post(
        `http://127.0.0.1:8000/api/${endpoint}`,
        payload,
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      if (isLogin) {
        if (response.status === 200) {
          const data = response.data;
          localStorage.setItem("accessToken", data.access);
          localStorage.setItem("refreshToken", data.refresh);
          localStorage.setItem("isLoggedIn", "true");
          setIsLoggedIn(true);
          toast.success("登录成功");
          onSuccess();
        }
      } else {
        if (response.status === 201) {
          toast.success("注册成功，请登录。");
          setIsLogin(true);
          setFormData({ username: "", password: "", confirmPassword: "" });
        }
      }
    } catch (error: any) {
      console.error(error);
      let errorMessage = isLogin ? "登录失败" : "注册失败";

      if (axios.isAxiosError(error) && error.response?.data) {
        const data = error.response.data;
        // 尝试提取后端返回的具体错误信息
        // Django 通常返回格式: { "password": ["密码太短..."], "username": ["已存在..."] }
        if (typeof data === "object" && data !== null) {
          const messages = Object.values(data).flat();
          if (messages.length > 0 && typeof messages[0] === "string") {
            errorMessage = messages[0] as string;
          }
        }
      }
      toast.error(errorMessage);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="relative w-full max-w-md p-8 bg-black/80 border border-blue-500/30 rounded-2xl backdrop-blur-md"
          >
            {/* Close button */}
            <button 
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-white"
            >
                ✕
            </button>

            <h2 className="text-3xl font-bold text-center mb-8 text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-blue-500">
              {isLogin ? "欢迎回来弈士" : "加入竞技场"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <input
                  type="text"
                  name="username"
                  placeholder="用户名"
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500/50 text-white placeholder-gray-500 transition-colors"
                />
              </div>
              <div>
                <input
                  type="password"
                  name="password"
                  placeholder="密码"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500/50 text-white placeholder-gray-500 transition-colors"
                />
              </div>
              

              {!isLogin && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                >
                  <input
                    type="password"
                    name="confirmPassword"
                    placeholder="确认密码"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500/50 text-white placeholder-gray-500 transition-colors"
                  />
                </motion.div>
              )}

              {!isLogin && (
                <div className="text-xs text-gray-400 px-1">
                  <p className="mb-1 text-blue-300/80">密码要求：</p>
                  <ul className="list-disc list-inside space-y-0.5 text-gray-500 pl-1">
                    <li>密码长度至少 8 位</li>
                    <li>密码不能仅包含数字</li>
                    <li>密码不能过于简单</li>
                  </ul>
                </div>
              )}

              <button
                type="submit"
                className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-400 hover:from-blue-500 hover:to-blue-300 text-white font-bold rounded-lg shadow-lg transform transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                {isLogin ? "登录" : "注册"}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-400 text-sm">
                {isLogin ? "还没有账号？ " : "已有账号？ "}
                <button
                  onClick={() => setIsLogin(!isLogin)}
                  className="text-blue-400 hover:text-blue-300 font-semibold underline decoration-transparent hover:decoration-blue-300 transition-all"
                >
                  {isLogin ? "去注册" : "去登录"}
                </button>
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
