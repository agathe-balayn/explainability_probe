import React, {useEffect, useState} from "react";
import { useHistory } from "react-router";
import { Button } from "antd";
import {Dropdown, DropdownButton} from "react-bootstrap";
import axios from "axios";
import {get_sessions_url} from "../API"

function UserProfile() {
  let history = useHistory();
  const [user, setUser] = useState(JSON.parse(sessionStorage.getItem("user")));
  let [available_sessions, set_available_sessions] = useState([])
  const [token, setToken] = useState(
    JSON.parse(sessionStorage.getItem("token"))
  );
  const [login_status, set_login_status] = useState(
    JSON.parse(sessionStorage.getItem("login_status"))
  );

  const get_available_predictions = (event) => {
    axios.post(
        get_sessions_url,
        {"user_id": user.id},

        {
            headers: {
                "Content-Type": "application/json" ,
                Authorization: "Token " + token
            }
        }
    )
        .then((response) => {
          const list_avail_sessions = response.data["result"]
          set_available_sessions_helper(list_avail_sessions)
        })
        .catch(function (exception) {
            const errors = document.getElementsByClassName("errorDiv")[0]
            errors.innerHTML = ""
            const error = document.createElement("div")
            error.className = "error"
            error.innerHTML = "You do not appear to have any available projects. Please add a new project or ask for " +
                "assistance if this is a mistake"
            errors.appendChild(error)
            set_available_sessions([])
        })

  }

  function set_available_sessions_helper(list_avail_sessions) {
    const arr = []
    for (let i = 0; i < list_avail_sessions.length; i++) {
      const new_arr = []
      new_arr[0] = list_avail_sessions[i].id
      new_arr[1] = list_avail_sessions[i].name
      arr[i] = new_arr
    }
    set_available_sessions(arr)
  }

  const logout_user = (e) => {
    sessionStorage.setItem("login_status", JSON.stringify(false));
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("session")
    history.push("/");
  };

  const user_selected_session = (event) => {
    const selected_session_user_id = event.target.value.split(" ")
    // make request to backend with this user id
    document.getElementById("headerWhole").innerHTML = selected_session_user_id[1]

  }

  const select_session = (e) => {
    const div = document.getElementsByClassName("errorDiv")[0]
    div.innerHTML = ""

    if (available_sessions.length > 0) {
        let selected = document.getElementById("sessionSelector").value.split(" ")
        document.getElementById("headerWhole").innerHTML = selected[1]
        sessionStorage.setItem("selected", JSON.parse("false"))
        sessionStorage.setItem("session", selected[0])
        window.location.href="/home?tab=1"
        //history.push('/home?tab=0')
    }
    else {
        const error = document.createElement("div")
        error.className = "error"
        error.innerHTML = "You are not subscribed to any projects. You can add one using the submit data tab."
        div.appendChild(error)
    }
  }

  useEffect(() => {
    get_available_predictions();
  }, [0]);

  return (
    <div>
      <div className="errorDiv">
      </div>
      <h2>Hello {user.username}! </h2>
      {user.seca_user.is_developer && (
      <div>
      <h3>
       As a Developer, you have subscribed to the following projects:
      </h3>
      </div>
      )}
      {!user.seca_user.is_developer && (
      <div>
      <h3>As an Expert, you have subscribed to the following projects:</h3>
      </div>
      )}
      <select onChange={user_selected_session} id={"sessionSelector"}>
        {
          available_sessions.map((session) =>
              <option value={session[0] + " " + session[1]}>{session[1]}</option>
          )
        }
      </select>
      <Button onClick={select_session}>Select</Button>
      <h1>Logout</h1>
      <Button onClick={logout_user}>Logout</Button>
    </div>
  );
}

export default UserProfile;
