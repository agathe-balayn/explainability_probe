import React from "react";
import ReactDOM from "react-dom";
import "./css/index.less";
import App from "./App";
import Notes from "./components/Notes";
import reportWebVitals from "./reportWebVitals";
import { Layout } from "antd";

const { Header, Content } = Layout;
//{/*JSON.parse(sessionStorage.getItem("problem_name"))*/}
ReactDOM.render(
        <Layout>
           <Header id={"headerWhole"}/>
          <Layout>
            <Content>
              <App />
            </Content>
            <Notes />
          </Layout>
        </Layout>,
  document.getElementById("root")
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
