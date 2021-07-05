import React from "react";
import { Route, useHistory } from "react-router-dom";
import { Button } from "antd";

import "../css/Welcome.less"
import {EyeFilled} from "@ant-design/icons";

function Welcome() {

  const history = useHistory();
  sessionStorage.setItem("selected", JSON.parse("true"))

  const login = (event) => {
    history.push("/login");
  };
  const register = (event) => {
    history.push("/register");
  };

  return (
    <div className={"welcomePages"}>
      <Route>
        <span>
          <EyeFilled style={{ fontSize: '50px', height: '100px' }} />
        </span>
        <h1>Welcome to the SECA interface!</h1>
        <h3>Please either login or register</h3>
        <Button onClick={login} type="primary" className="btn">Login</Button>
        <Button onClick={register} className="btn">Register</Button>
        <br/>
        <Button id="extraButton" className="btn">Button</Button>
      </Route>
    </div>
  );
}

export default Welcome;
