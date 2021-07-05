import React from 'react';
import { Layout } from 'antd';
import { Input } from 'antd';
import { Button } from 'antd';
import {notes_url} from "../API";

const { TextArea } = Input;
const { Sider} = Layout;

class Notes extends React.Component {

    constructor() {
        super();
        this.state = {
            user: JSON.parse(sessionStorage.getItem("user")),
            token: JSON.parse(sessionStorage.getItem("token")),
            login_status: JSON.parse(sessionStorage.getItem("login_status")),
            sessionId:  JSON.parse(sessionStorage.getItem("session")),
            notes : "",
            collapsed : true,
            fetched: 0
        };
    }

    saveNotes = () => {
        let body = {
            "username" : this.state.user.username,
            "session_id" : this.state.sessionId,
            "notes" : document.getElementById("notes").value
        }
        fetch(notes_url+"/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": JSON.parse(sessionStorage.getItem("token"))
                },
            body: JSON.stringify(body)
        }).then((data) => data.json())
            .then(res => {
                document.getElementById("savedAlert").innerHTML = "Saved!"
            })
    }

    getNotes = (e) => {
        if(this.state.notes.length === 0) {
            fetch(notes_url + "?user=" + this.state.user.username + "&session_id=" + this.state.sessionId, {
                method: "GET",
                headers: {"Content-Type": "application/json", "Authorization": JSON.parse(sessionStorage.getItem("token"))}
            }).then((data) => data.json())
                .then(res => {
                    this.setState({
                        notes: res.notes,
                        fetched: 1
                    })
                })
        }


    }

    state = {
        collapsed: true,
    };

    onCollapse = (collapsed) => {
        this.getNotes()
        this.setState({ collapsed : collapsed});
    };

    editNotes = (e) => {
        document.getElementById("savedAlert").innerHTML = "Save your changes"
    }


    render() {
        const { collapsed } = this.state;
        let notes_view = []
        let notes = this.state.fetched
        if(notes > 0){
            notes_view.push(<TextArea rows={30} id="notes" key={"notes"} onChange={this.editNotes} defaultValue={this.state.notes}/>)
        }
        return (
                <Sider collapsible collapsed={collapsed} onCollapse={this.onCollapse} reverseArrow={true} collapsedWidth="0">
                    {notes_view}
                    <Button type="primary" onClick={this.saveNotes}>Save</Button>
                    <p style={{"color": "white", "fontSize": "15px"}} id={"savedAlert"}/>
                </Sider>
        );
    }
}

export default Notes;