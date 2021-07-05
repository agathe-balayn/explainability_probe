import React from "react";
import ClassSpecificExplanations from "./ClassSpecificExplanations";
import OverallExplanations from "./OverallExplanations";
import { Tabs } from "antd";

const { TabPane } = Tabs;

function callback(key) {
  console.log(key);
}

function Explore() {
  return (
    <div className="App">
      <header className="App-header">
        <Tabs
          defaultActiveKey="1"
          onChange={callback}
          type="card"
          className="overall_explanations"
        >
          <TabPane tab="Overall Explanations" key="1">
            <OverallExplanations />
          </TabPane>
          <TabPane tab="Class Specific Explanations" key="2">
            <ClassSpecificExplanations />
          </TabPane>
        </Tabs>
      </header>
    </div>
  );
}

export default Explore;
