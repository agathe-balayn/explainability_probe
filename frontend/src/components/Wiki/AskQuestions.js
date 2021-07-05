import React from 'react';
import {Input} from 'antd';
import { Button } from 'antd';

import "../../css/ExpertBackground.less"
import {expert_questions_url } from "../../API";
import axios from "axios";
const { TextArea } = Input;
class AskQuestions extends React.Component {

    constructor() {
        super();
        this.state = {
            user: JSON.parse(sessionStorage.getItem("user")),
            token: JSON.parse(sessionStorage.getItem("token")),
            login_status: JSON.parse(sessionStorage.getItem("login_status")),
            session_id: JSON.parse(sessionStorage.getItem("session")),
            questions: []
        };
    }

    rows = []

    done = false;

    /**
     * get data from backend
     * @param event
     */
    getAllQuestions(event) {
        if (!this.done) {
            fetch(expert_questions_url + "?session_id=" + this.state.session_id, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": JSON.parse(sessionStorage.getItem("token"))
                },
            }).then(res => res.json())
                .then(res => {
                    this.setState({
                        questions: res.questions,
                    });
                }).then(this.done = true).catch(function (exception) {
                            const errors = document.getElementsByClassName("errorDiv")[2]
                            errors.innerHTML = ""
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the request. Try again later."
                            errors.appendChild(error)
                    })
        }

    }

    /**
     * send a new question to backend
     * @param e
     */
    addQuestion = (e) => {
        let question = document.getElementById("question0").value
        let answer = ""
        let session_id = this.state.session_id
        axios
            .post(expert_questions_url, JSON.stringify({session_id, question, answer}), {
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Token " + this.state.token
                },
            })
            .then(res => {
                let arr = this.state.questions
                arr.push({
                    "question": question, "answer": ""
                })
                this.setState({
                    questions: arr
                })
            })
    }

    /**
     * create row in table
     * @param type type of row (is displayed on button)
     * @param question the content of the question
     * @param answer the content of the answer
     * @param id the id of the row
     * @returns {JSX.Element} the row of the table
     */
    tableRow(type, question, answer, id) {
        const onClick = e => {
            let question = document.getElementById("question" + id).innerHTML
            let answer = document.getElementById("answer" + id).value
            let session_id = this.state.session_id
            axios
                .post(expert_questions_url, JSON.stringify({session_id, question, answer}), {
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Token " + this.state.token
                    },
                })
                .then(res => {
                    alert("saved successfully")
                })

        }
        let session_id = this.state.session_id

        /**
         * remove request to backend
         * @param e
         */
        function removeRow(e) {
            let question = document.getElementById("question" + id).innerHTML
            if (window.confirm('Are you sure you want to remove this question?')) {
                axios
                    .delete(expert_questions_url + "?question=" + question + "&session_id=" + session_id, {
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": "Token " + this.state.token
                        },
                    }).then(function () {
                    document.getElementById('questionTable').removeChild(document.getElementById('questionRow' + id))
                })
            }
        }

        return (
            <tr id={"questionRow" + id} key={id}>
                <td>
                    <p id={"question" + id}>{question}</p>
                </td>
                <td>
                    {this.state.user.seca_user.is_developer &&
                    <p>{answer}</p>}
                    {!this.state.user.seca_user.is_developer &&
                    <TextArea rows={5} className="answer" id={"answer" + id} defaultValue={answer}/>}
                </td>
                <td>
                    {!this.state.user.seca_user.is_developer &&
                    <Button type="primary" onClick={onClick} id={"questionSaveButton" + id}>{type}</Button>}
                </td>
                <td id={"questionRemove" + id} onClick={removeRow}><Button>X</Button></td>
            </tr>
        )
    }

    render() {
        let rowList = []

        for (let i = 0; i < this.state.questions.length; i++) {
            rowList.push(
                this.tableRow("answer", this.state.questions[i]['question'],
                    this.state.questions[i]['answer'], (i + 1))
            )
        }

        this.getAllQuestions()
        return (
            <div>
                <div className="errorDiv">
                </div>
                {this.state.user.seca_user.is_developer && <h1>Ask a question</h1>}
                {!this.state.user.seca_user.is_developer && <h1>Answer a question</h1>}
                <div>
                </div>
                {this.state.user.seca_user.is_developer &&
                <TextArea placeholder={"ask a quesion here..."} id={"question0"}/>}
                {this.state.user.seca_user.is_developer &&
                <Button onClick={this.addQuestion} type="primary">ask</Button>}
                <table id={"questionTable"}>
                    <tr>
                        <th>
                            Question
                        </th>
                        <th>
                            Answer
                        </th>
                    </tr>
                    {rowList}
                </table>
                <div id={"attempt"}/>
            </div>
        )
    }
}

export default AskQuestions;