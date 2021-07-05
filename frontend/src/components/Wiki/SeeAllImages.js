import React from 'react';
import { Collapse } from 'antd';
import { InputNumber, Button, Space } from 'antd';
import { see_all_images as see_all_images_url } from "../../API";
import "../../css/ExpertBackground.less"

const { Panel } = Collapse;

class SeeAllImages extends React.Component {

    constructor() {
        super();
        this.state = {
            user: JSON.parse(sessionStorage.getItem("user")),
            token: JSON.parse(sessionStorage.getItem("token")),
            login_status: JSON.parse(sessionStorage.getItem("login_status")),
            session_id: JSON.parse(sessionStorage.getItem("session")),
            data: ""
        };
    }

    getAllImages = (event) => {
        let num = document.getElementById("input").value;
        fetch(see_all_images_url + "?amount=" + num +"&session_id=" + this.state.session_id, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": JSON.parse(sessionStorage.getItem("token"))
            },
            }).then((data) => data.json())
            .then(data => {
                document.getElementById("seeall").innerHTML = '';
                for(let i = 0; i < data['images'].length; i+=2){
                    let img = document.createElement('img');
                    let tr = document.createElement('tr');
                    let td = document.createElement('td');
                    let td2 = document.createElement('td');
                    let img2 = document.createElement('img');

                    if(data['images'].length > i+1){
                        td2.appendChild(img2)
                        tr.appendChild(td2);
                        img2.src = 'data:image/jpeg;base64,' + data['images'][i+1]
                    }
                    td.appendChild(img);
                    tr.appendChild(td);
                    img.src = 'data:image/jpeg;base64,' + data['images'][i]
                    document.getElementById("seeall").appendChild(tr)
                }
            })
    };

    render() {
        return (
            <Collapse>
                <Panel header="See All Images" key="1" id={"seeAllImages"}>
                    <Space>
                        <InputNumber min={1} max={1000} defaultValue={3} id="input"/>
                        <Button type="primary" onClick={this.getAllImages}>Get Images</Button>
                    </Space>
                    <table id={"seeall"}>
                    </table>
                </Panel>
            </Collapse>
        )
    }
}

export default SeeAllImages;