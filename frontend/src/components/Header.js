import { EyeFilled } from "@ant-design/icons";
import { Tabs } from "antd";
import React, {useState} from "react";
import AboutInterface from "./AboutInterface";
import AboutSECA from "./AboutSeca";
import ConfusionMatrix from "./ConfusionMatrix/ConfusionMatrix";
import Query from "./Query/Query";
import Wiki from "./Wiki/Wiki";
import Tutorial from "./interface_7/Tutorial"
import UserProfile from "./UserProfile";
import SubmitData from "./SubmitData";
import Dashboard from "./Dashboard";
import Explore from "./Explore/Explore";
const { Tab, TabPane } = Tabs;

export default function Header(props) {
    const q = window.location.search;
    let urlParams = new URLSearchParams(q);
    let tab = urlParams.get("tab");

    const[selected, setSelected] = useState(sessionStorage.getItem("selected"))

    const callback = (key) => {
        window.location.href = "?tab=" + key;
    };


    return (
        <Tabs activeKey={tab} id="home_tabs" onChange={callback} type="card">
            <TabPane disabled={selected !="false"} tab={<span><EyeFilled />About</span>} key="0" className="home_tab" id={"home_tab"}>
                <div className="tabBody">
                    <AboutInterface />
                </div>
            </TabPane>
            <TabPane disabled={selected !="false"} tab="Dashboard" key="1" className="dashboard_tab" id={"dashboard_tab"}>
                <div className="tabBody">
                    <Dashboard />
                </div>
            </TabPane>

            <TabPane disabled={selected !="false"} tab="SECA" key="2" className="home_tab">
                <div className="tabBody">
                    <AboutSECA />
                </div>
            </TabPane>
            <TabPane disabled={selected !="false"} tab="Confusion Matrix" key="3" className="home_tab">
                <div className="tabBody">
                    <ConfusionMatrix/>
                </div>
            </TabPane>
            <TabPane disabled={selected !="false"} tab="Explore" key="4" class="home_tab">
                <div className="tabBody"><Explore /></div>
            </TabPane>
            <TabPane disabled={selected !="false"} tab="Query" key="5" class="home_tab">
                <div className="tabBody">
                    <Query />
                </div>
            </TabPane>
            <TabPane disabled={selected !="false"} tab="Wiki" key="6" class="home_tab">
                <div className="tabBody">
                    <Wiki />
                </div>
            </TabPane>
            <TabPane disabled={selected !="false"} tab="Info" key="7" class="home_tab">
                <div className="tabBody">
                    <Tutorial />
                </div>
            </TabPane>
            <TabPane tab="User Profile" key="8" class="home_tab">
                <div className="tabBody">
                    <UserProfile />
                </div>
            </TabPane>
            <TabPane tab="Submit data" key="9">
                <div className="tabBody">
                    <SubmitData />
                </div>
            </TabPane>
        </Tabs>
    );
}
