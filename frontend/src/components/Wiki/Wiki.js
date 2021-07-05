import React from 'react';
import ExpertBackground from "./ExpertBackground";
import EditWiki from "./EditWiki";
import AskQuestions from "./AskQuestions"
import { Tabs } from 'antd';
const { TabPane } = Tabs;


class Wiki extends React.Component {
    constructor() {
        super();
        this.state = {
            user: JSON.parse(sessionStorage.getItem("user")),
            token: JSON.parse(sessionStorage.getItem("token")),
            login_status: JSON.parse(sessionStorage.getItem("login_status")),
        };
    }

    render() {
        let questionTabText = ""
        if(this.state.user.seca_user.is_developer) questionTabText = "Ask questions"; else questionTabText = "Answer questions"
        return (
           <div className="App">
              <header className="App-header">
                  <Tabs defaultActiveKey="1" type="card" className="wiki_tabs">
                      <TabPane tab="Expert Background" key="1">
                          <ExpertBackground />
                      </TabPane>
                      <TabPane tab="Edit" key="2">
                          <EditWiki />
                      </TabPane>
                      <TabPane tab={questionTabText} key="3">
                          <AskQuestions />
                      </TabPane>
                    </Tabs>
              </header>
            </div>
        );
    }
}

export default Wiki;
