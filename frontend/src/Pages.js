import React from "react";
import {
  BrowserRouter as Router,
  Route,
  Switch,
  Redirect,
} from "react-router-dom";

import Home from "./components/Home";
import Welcome from "./components/Welcome";
import Register from "./components/login_registration/Register";
import Login from "./components/login_registration/Login";
import ProtectedRoutes from "./components/authentication/ProtectedRoutes";
import Classification from "./components/ConfusionMatrix/Classification";
import CorrectClassification from "./components/ConfusionMatrix/CorrectClassification";

function Pages() {
  return (
    <div>
      <Router>
        <Switch>
            {/* Add paths here that load components that are visible to anyone */}
            <Route
                path="/"
                exact
                render={(props) => {
                  let isAuth = JSON.parse(sessionStorage.getItem("login_status"));
                  if (isAuth) {
                    return (
                      <Redirect
                        to={{ pathname: "/home", state: { from: props.location } }}
                      />
                    );
                  } else {
                    return <Welcome />;
                  }
                }}
            />
            <Route path="/login" exact component={Login} />
            <Route path="/register" exact component={Register} />
            {/* Add paths here that load components that require user authentication */}
            <ProtectedRoutes path="/home" component={Home} />
            <ProtectedRoutes path="/home?tab=:tab" component={Home} />
            <ProtectedRoutes path="/classification/:row/:col" component={Classification} />
            <ProtectedRoutes path="/correct-classification/:row/:col" component={CorrectClassification} />
            <Route path="*" component={() => "404 NOT FOUND"} />
        </Switch>
      </Router>
    </div>
  );
}

export default Pages;
