import axios from "axios";
import React, { useState} from "react";
import { useHistory } from "react-router";
import { Button } from "antd";
import { new_user as new_user_url } from "../../API";

import "../../css/Welcome.less"

function Register(props) {
  const bcrypt = require('bcryptjs');
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  let history = useHistory();


  const register = (event) => {
    var role = document.getElementById("role").value;
    var seca_user = null;
    const salt = bcrypt.genSaltSync();
    const hashedPassword = bcrypt.hashSync(password, salt);
    const errorDiv = document.getElementsByClassName("errorDiv")[0];
    errorDiv.innerHTML = ""

    if (role === "developer") {
      seca_user = {
        is_developer: true,
        developer: {},
      };
    } else if (role === "expert") {
      seca_user = {
        is_developer: false,
        expert: {},
      };
    }
    setPassword(hashedPassword);


    axios
      .post(
        new_user_url,
        JSON.stringify({ username, password, seca_user }),
        {
          headers: { "Content-Type": "application/json" },
        }
      )
      .then(function (response) {
        const e = document.createElement("div")
        e.innerHTML = "User creation successful, now directing you to the login page"
        e.className = "success"
        errorDiv.appendChild(e)
        history.push({
          pathname: "/login",
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
        } else {
          alert("Something went wrong, please try again");
        }
      });
  };

  const back = (event) => {
    history.push({
      pathname: "/",
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
      register(e);
    }
  }

  return (
    <div>
    <div className={"errorDiv"}>
    </div>

    <div className={"welcomePages"}>
      <h2>Register Here</h2>
      <label>
        Username:
        <input
          type="text"
          name="username"
          onChange={updateUsername}
        />
      </label>
      <br />
      <label id="register">
        Password:
        <input
          type="password"
          name="password"
          onChange={updatePassword}
          onKeyPress={handleKeypress}
        />
      </label>
      <br />
      <label>
        Please select a role:
        <select id="role">
          <option value="developer">developer</option>
          <option value="expert">expert</option>
        </select>
      </label>
      <br />
      <Button onClick={register} type="primary" className="btn" id="registerBtn">Register</Button>
      <Button onClick={back} className="btn">Back</Button>
    </div>
    </div>
  );
}

export default Register;
