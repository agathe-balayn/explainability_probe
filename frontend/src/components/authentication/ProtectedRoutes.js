import React from "react";
import { Route, Redirect } from "react-router-dom";

function ProtectedRoutes({ component: Component, ...rest }) {
  return (
    <Route
      {...rest}
      render={(props) => {
        let isAuth = JSON.parse(sessionStorage.getItem("login_status"));
        if (isAuth) {
          return <Component {...props} />;
        } else {
          return (
            <Redirect to={{ pathname: "/", state: { from: props.location } }} />
          );
        }
      }}
    />
  );
}

export default ProtectedRoutes;
