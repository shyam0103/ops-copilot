// src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Verify token on mount
      verifyToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/auth/whoami", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(res.data);
    } catch (error) {
      console.error("Token verification failed:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);

    const res = await axios.post(
      "http://127.0.0.1:8000/auth/login",
      formData
    );

    const newToken = res.data.access_token;
    localStorage.setItem("token", newToken);
    setToken(newToken);

    // Get user info
    const userRes = await axios.get("http://127.0.0.1:8000/auth/whoami", {
      headers: { Authorization: `Bearer ${newToken}` },
    });
    setUser(userRes.data);

    return userRes.data;
  };

  const register = async (email, password) => {
    const res = await axios.post("http://127.0.0.1:8000/auth/register", {
      email,
      password,
    });

    const newToken = res.data.access_token;
    localStorage.setItem("token", newToken);
    setToken(newToken);

    // Get user info
    const userRes = await axios.get("http://127.0.0.1:8000/auth/whoami", {
      headers: { Authorization: `Bearer ${newToken}` },
    });
    setUser(userRes.data);

    return userRes.data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, token, login, register, logout, loading }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}; 
