"use client"
import React, { useContext, useEffect, useState } from "react";
import "./styles.css"; 
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthContext } from "../contexts/AuthContext";
import axios from "axios";
import { toast} from "sonner";
const LoginPage = () => {
  const { isLoggedIn,setIsLoggedIn } = useContext(AuthContext);
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });

  const router = useRouter();
  useEffect(() => {
    if (isLoggedIn) {
      router.replace("/");
      document.body.style.overflow = "auto";
    }
  }, [isLoggedIn, router]);
  
  // Handle input changes
  const handleChange = (e:React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e:React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const { username, password } = formData;

    if (!username || !password) {
      toast.error("请填写所有字段");
      return; // 添加return阻止继续执行
    }

    try { 
      const response = await axios.post(
        `http://localhost:8000/api/login/`, //peropero's change
        {
          username,
          password,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
          withCredentials: true, 
        }
      );
      
      const data = await response.data;

      if (response.status==200) {
        localStorage.setItem("accessToken", data.access);
        localStorage.setItem("refreshToken", data.refresh);
        localStorage.setItem("isLoggedIn", "true");
        localStorage.setItem("username", formData.username);

        toast.success("登录成功")
        setIsLoggedIn(true);
      } else {
        toast.error("发生错误")
      }
    } catch (err: any) {
      console.log(err)
      if (err.response && err.response.data && err.response.data.detail) {
        toast.error(err.response.data.detail);
      } else {
        toast.error("无法连接到服务器");
      }
    }
    finally{
    }
  };

  return (
    <div className="mainbox">
      <div className="ring">
        <i className="ring-item"></i>
        <i className="ring-item"></i>
        <i className="ring-item"></i>

        <div className="login">
          <h2>Login</h2>
          <form onSubmit={handleSubmit}>
            <div className="inputBx">
              <input
                type="text"
                placeholder="Username"
                name="username"
                value={formData.username}
                onChange={handleChange}
              />
            </div>
            <div className="inputBx">
              <input
                type="password"
                placeholder="Password"
                name="password"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
            <div className="inputBx">
              <input type="submit" value="Login" />
            </div>
          </form>
          <div className="links">
            Don't have an account?
            <Link className="link" href="/signup">
              {" "}
              Signup
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(LoginPage);
