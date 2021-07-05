import React, { useState, createContext } from "react";

export const AuthContext = createContext();

export const AuthProvider = (props) => {
  const [user, setUser] = useState({});
  const [login_status, set_login_status] = useState(false);
  const [token, setToken] = useState("");

  return (
    <AuthContext.Provider
      value={{
        user_info: [user, setUser],
        login_info: [login_status, set_login_status],
        token_info: [token, setToken],
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
};
