import React, { useState } from "react";
import { useHistory } from "react-router";
import "../../css/Welcome.less"
import { Button } from "antd";
import { EyeFilled } from '@ant-design/icons';
import { auth as auth_url } from "../../API";

const axios = require("axios").default;

function Login(props) {
  const bcrypt = require('bcryptjs');
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  let history = useHistory();

  const back = (event) => {
    history.push({
      pathname: "/",
    });
  }

  const login = (event) => {
    const salt = bcrypt.genSaltSync();
    const hashedPassword = bcrypt.hashSync(password, salt);
    setPassword(hashedPassword);
    const errorDiv = document.getElementsByClassName("errorDiv")[0];
    errorDiv.innerHTML = ""
    axios
      .post(auth_url, JSON.stringify({ username, password }), {
        headers: { "Content-Type": "application/json" },
      })
      .then(function (response) {
        sessionStorage.setItem("user", JSON.stringify(response.data.user));
        sessionStorage.setItem("token", JSON.stringify(response.data.token));
        sessionStorage.setItem("login_status", JSON.stringify(true));
        history.push({
          pathname: "/home?tab=8",
        });
      })
      .catch(function (error) {
        if (error.response) {
          if (error.response.data.username != null) {
            if (error.response.data.username.includes("This field may not be blank.")) {

                const e = document.createElement("div")
                e.innerHTML = "Username cannot be empty."
                e.className = "error"
                errorDiv.appendChild(e)

            }
          }
          if (error.response.data.password != null) {
            if (error.response.data.password.includes("This field may not be blank.")) {

                const e = document.createElement("div")
                e.innerHTML = "password cannot be empty."
                e.className = "error"
                errorDiv.appendChild(e)

            }
          }
          if (error.response.data.non_field_errors != null) {
            if (error.response.data.non_field_errors.includes("Unable to log in with provided credentials.")) {

                const e = document.createElement("div")
                e.innerHTML = "Unable to log in with provided credentials. Make sure the spelling is correct."
                e.className = "error"
                errorDiv.appendChild(e)

            }
          }
        } else {
          alert("Something went wrong, please try again");
        }
      });
  };

  const updateUsername = (event) => {
    setUsername(event.target.value);
    setPassword(password);
  };

  const updatePassword = (event) => {
    setPassword(event.target.value);
    setUsername(username);
  };

  const handleKeypress = e =>  {
    if (e.key === 'Enter') {
      login(e);
    }
  }

  return (
      <div>
        <div className={"errorDiv"}>
        </div>
        <div className={"welcomePages"}>
        <span>
          <EyeFilled style={{ fontSize: '50px', height: '100px' }} />
        </span>
        <h2>Login Here</h2>
        <label>
          Username:
          <input
              type="text"
              name="username"
              onChange={updateUsername}
          />
        </label>
        <br/>
        <label id="login">
          Password:
          <input
              type="password"
              name="password"
              onChange={updatePassword}
              onKeyPress={handleKeypress}
          />
        </label>
        <br/>
        <Button onClick={login} type="primary" className="btn" id={"loginBtn"}>Login</Button>
        <Button onClick={back} className="btn">Back</Button>
      </div>
      </div>
  );
}

export default Login;
