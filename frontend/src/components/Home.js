import React from "react";
import Header from "./Header";
import "../css/Home.less"

class Home extends React.Component {
  constructor() {
    super();
    this.state = {
      user: JSON.parse(sessionStorage.getItem("user")),
      token: JSON.parse(sessionStorage.getItem("token")),
      login_status: JSON.parse(sessionStorage.getItem("login_status")),
    };
  }

  render() {
        return (
            <div className="App">
                <header className="App-header">
                    <Header />
                </header>
            </div>
        );
    }
}

export default Home;
