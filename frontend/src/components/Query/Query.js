import React from 'react';
import { Tabs } from 'antd';
import "../../css/QueryClassificatuonFormulas.less"
import QueryClassificationFormulas from "./QueryClassificationFormulas";
import QuerySpecificImage from "./QuerySpecificImage";

const { TabPane } = Tabs;

function callback(key) {
    console.log(key);
}

class Query extends React.Component {

    render() {

        return (
            <div className="App">
                <header className="App-header">
                    <Tabs defaultActiveKey="1" onChange={callback} type="card" className="wiki_tabs">
                        <TabPane tab="Query Classification Formulas" key="1">
                            <QueryClassificationFormulas />
                        </TabPane>
                        <TabPane tab="Query Specific Image" key="2">
                            <div>
                                <QuerySpecificImage />
                            </div>
                        </TabPane>
                    </Tabs>
                </header>
            </div>
        );
    }
}

export default Query;
