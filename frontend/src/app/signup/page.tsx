"use client"
import React, { useState } from "react";
import "../login/styles.css"; // Ensure this CSS file exists in the correct path
import Link from "next/link";
import axios from "axios";
import { toast } from "sonner";

const SignupPage = () => {

  const [formData, setFormData] = useState({
    username: "",
    password: "",
    confirmPassword: "",
  });


  const handleChange = (e:React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const { username, password, confirmPassword } = formData;

    // Basic validation
    if (!username || !password || !confirmPassword) {
      toast.warning("请填写所有字段");
      return;
    }

    try {
      const response = await axios.post(
        `http://localhost:8000/api/signup/`, //peropero's change
        {
          username,
          password,
          confirm_password: confirmPassword,
        } ,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.data;

      if (response.status==201) {
        toast.success("注册成功")
        window.location.href = "/login";
      } else {
        // Handle backend errors
        toast.error("注册过程中发生错误");
      }
    } catch (err: any) {
      console.log(err);
      if (err.response && err.response.data) {
        // 尝试提取后端返回的具体错误信息
        const errors = err.response.data;
        if (typeof errors === 'object') {
           // 遍历错误对象，显示第一个错误
           const firstKey = Object.keys(errors)[0];
           const firstError = errors[firstKey];
           if (Array.isArray(firstError)) {
             toast.error(firstError[0]);
           } else if (typeof firstError === 'string') {
             toast.error(firstError);
           } else {
             toast.error("注册失败，请检查输入");
           }
        } else {
           toast.error("注册失败");
        }
      } else {
        toast.error("无法连接到服务器");
      }
    }
  };

  return (
    <div className="mainbox">
      <div className="ring">
        <i className="ring-item"></i>
        <i className="ring-item"></i>
        <i className="ring-item"></i>

        <div className="login">
          <h2>注册</h2>
          <form onSubmit={handleSubmit}>
            <div className="inputBx">
              <input
                type="text"
                placeholder="用户名"
                name="username"
                value={formData.username}
                onChange={handleChange}
              />
            </div>
            <div className="inputBx">
              <input
                type="password"
                placeholder="密码"
                name="password"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
            <div className="inputBx">
              <input
                type="password"
                placeholder="确认密码"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
              />
            </div>
            <div className="inputBx">
              <input type="submit" value="注册" />
            </div>
          </form>
          <div className="links">
            已有账号？
            <Link className="link" href="/login">
              {" "}
              去登录
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(SignupPage);
