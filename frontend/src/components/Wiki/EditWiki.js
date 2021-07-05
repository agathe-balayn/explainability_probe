import React from 'react';
import {Input} from 'antd';
import { Button } from 'antd';

import "../../css/ExpertBackground.less"
import {add_wiki as add_wiki, remove_wiki, expertBackground, updateTitle_url } from "../../API";
import axios from "axios";
const { TextArea } = Input;

class EditWiki extends React.Component {
    constructor() {
        super();
        this.state = {
            user: JSON.parse(sessionStorage.getItem("user")),
            token: JSON.parse(sessionStorage.getItem("token")),
            login_status: JSON.parse(sessionStorage.getItem("login_status")),
            session_id: JSON.parse(sessionStorage.getItem("session")),
            data: [],
            rows: []
        };
    }
    state = {
        numConcepts: 0,
    }


    done = false;

    /**
     * save the title and intro based on the input on the screen
     * @param e
     */
    saveTitleIntro = (e) => {
        let title = document.getElementById("TitleInput").value
        let intro = document.getElementById("introInput").value
        axios.put(updateTitle_url, {"title" : title, "intro" : intro, "session_id" : this.state.session_id},
            {
                headers: {
                    "Content-Type": "application/json" ,
                    Authorization : "Token " + this.state.token
                }
        })
    }

    /**
     * get all data to display
     * @param event
     */
    getInformation(event) {
        if (!this.done) {
            fetch(expertBackground + "?session_id=" + this.state.session_id, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": JSON.parse(sessionStorage.getItem("token"))
                },
            }).then(res => res.json())
                .then(res => {
                    let rows = []
                    for (let i = 0; i < (res)['contents'].length; i++) {
                        let row = res['contents'][i]
                        rows.push(row)
                    }
                    this.setState({
                        numConcepts: (res)['contents'].length,
                        data: res,
                        rows : rows
                    });
                }).then(this.done = true)
                .catch(function (exception) {
                            const errors = document.getElementsByClassName("errorDiv")[1]
                            errors.innerHTML = ""
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the request. Try again later."
                            errors.appendChild(error)
                    })
        }

    }

    /**
     * create row in table
     * @param type type of row (is displayed on button)
     * @param class_name the name of the class
     * @param description description of the class
     * @param expert_concepts concepts suggested by expert
     * @param image image source in base64 encoding
     * @param id id of the row
     * @returns {JSX.Element} the row of the table
     */
    tableRow(type, class_name, description, expert_concepts, image, id){
        let img = ""
        if(image !== "none") {
            img = <img src={'data:image/jpeg;base64,' + (image)} style={{width: 150}} alt={"image of concept"}/>
        }

        let file = null

        function fileUpload(e){
            const fileTemp = e.target.files[0]
            const reader = new FileReader();

            reader.addEventListener("load", function(){
                let fileString = reader.result
                let fileArr = fileString.split(",")
                file = fileArr[1]
            })
            if(fileTemp){
                reader.readAsDataURL(fileTemp)
            }
        }

        let session_id = this.state.session_id

        const onClick = e => {
            let className = document.getElementById("class" + id).value
            let description = document.getElementById("description" + id).value
            let concepts = document.getElementById("concepts" + id).value
            let warned = false
            if (file == null) {
                if (type === "add") {
                    warned = true
                } else {
                    file = "no change"
                }
            }
            if (className === "" || description === "" || concepts === "" || warned) {
                alert("You have left some fields empty");
            } else {
                axios
                    .post(add_wiki, JSON.stringify({file, className, description, concepts, session_id}), {
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": "Token " + this.state.token
                        },
                    })
                    .then(res => {
                        let arr = this.state.rows
                        arr.push({"image" : file, "class" : className,"description" : description,"expert concepts" : concepts})
                        this.setState({
                            rows: arr,
                            numConcepts: this.state.numConcepts +1
                        })
                    })
            }
        }

        function removeRow(e){
            let className = document.getElementById("class" + id).value
            if (window.confirm('Are you sure you want to remove this row?')) {
                axios
                    .delete(remove_wiki + "?class=" + className + "&session_id=" + session_id, {
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": "Token " + this.state.token
                        },
                    }).then(function () {
                    document.getElementById('editTable').removeChild(document.getElementById('row'+id))
                })
            }
        }

        return (
            <tr id={"row"+id}>
                <td>
                    <TextArea rows={5} className="class" defaultValue={class_name} id={"class" + id}/>
                </td>
                <td>
                    <TextArea rows={5} className="description" id={"description" + id} defaultValue={description}/>
                </td>
                <td>
                    <TextArea rows={5} className="concepts" id={"concepts"+id} defaultValue={expert_concepts}/>
                </td>
                <td>
                    {img}
                </td>
                <td>
                    <input type={"file"} id={"file" + id} onChange={fileUpload} />
                </td>
                <td>
                    <Button type="primary" onClick={onClick} id={"saveButton" + id}>{type}</Button>
                </td>
                <td id={"remove" + id} onClick={removeRow}> <Button>X</Button></td>
            </tr>
        )
    }

    render() {
        let rowListContent = this.state.rows
        let rowList = []
        let editTopView = []
        if(this.state.numConcepts > 0) {
            editTopView.push(<Input id={"TitleInput"} defaultValue={this.state.data['title']} size={"large"}/>)
            editTopView.push(<TextArea id={"introInput"} rows={5} defaultValue={this.state.data['intro']}/>)
            editTopView.push(<Button id={"saveButton"} type="primary" onClick={this.saveTitleIntro}>Save title and
                intro</Button>)
        }

        for(let i = 0; i < this.state.numConcepts; i++) {
            rowList.push(
                this.tableRow("save", rowListContent[i]['class'],
                    rowListContent[i]['description'], rowListContent[i]['expert concepts'],
                    rowListContent[i]['image'], (i+1))
            )
        }

        this.getInformation()
        return (
            <div>
                <div className="errorDiv">
                </div>
                <h1>Create new class description or edit an existing one</h1>
                <div>
                    {editTopView}
                </div>
                <table id={"editTable"}>
                    <tr>
                        <th>
                            Class
                        </th>
                        <th>
                            General Description
                        </th>
                        <th>
                            Expected concepts
                        </th>
                        <th>
                            Old Image
                        </th>
                        <th>
                            New Image
                        </th>
                    </tr>
                    {this.tableRow("add", "", "", "", "none", 0)}
                    {rowList}
                </table>
                <div id={"attempt"}> </div>
            </div>
        )
    }
}

export default EditWiki;