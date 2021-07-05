import React from 'react';
import "../../css/ExpertBackground.less"
import SeeAllImages from "./SeeAllImages"
import {expertBackground } from "../../API";

class ExpertBackground extends React.Component {
    //should all come from backend
    constructor() {
        super();
        this.state = {
            user: JSON.parse(sessionStorage.getItem("user")),
            token: JSON.parse(sessionStorage.getItem("token")),
            login_status: JSON.parse(sessionStorage.getItem("login_status")),
            session_id: JSON.parse(sessionStorage.getItem("session")),
        };
    }
    done = false;
    getInformation = (event) => {
        if(!this.done) {
            fetch(expertBackground + "?session_id=" + this.state.session_id, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": JSON.parse(sessionStorage.getItem("token"))
                },
            }).then(res => res.json())
                .then(res => {
                    console.log(res)
                    document.getElementById("title").innerHTML = res['title']
                    document.getElementById("intro").innerHTML = res['intro']
                    for (let i = 0; i < (res)['titles'].length; i++) {
                        let th = document.createElement('th')
                        th.innerHTML = res['titles'][i]
                        document.getElementById('data_table').appendChild(th)
                    }
                    for (let i = 0; i < (res)['contents'].length; i++) {
                        let tr = document.createElement("tr")
                        let td1 = document.createElement("th")
                        let td2 = document.createElement("td")
                        let td3 = document.createElement("td")
                        let td4 = document.createElement("td")
                        let img = document.createElement("img")

                        td1.innerHTML = res['contents'][i]['class']
                        td2.innerHTML = res['contents'][i]['description']
                        td3.innerHTML = res['contents'][i]['expert concepts']
                        img.src = 'data:image/jpeg;base64,' + (res['contents'][i]['image'])
                        td4.appendChild(img)
                        tr.appendChild(td1)
                        tr.appendChild(td2)
                        tr.appendChild(td3)
                        tr.appendChild(td4)
                        document.getElementById("data_table").appendChild(tr)
                    }
                }).then(this.done = true)
                .catch(function (exception) {
                            const errors = document.getElementsByClassName("errorDiv")[0]
                            errors.innerHTML = ""
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the request. Try again later."
                            errors.appendChild(error)
                    })

        }

    }

    render() {
            this.getInformation()
            return (
                <div id="ExpertBackground">
                    <div className="errorDiv">
                    </div>
                    <h2 id="title"> </h2>
                    <p id = "intro"> </p>
                    <SeeAllImages />
                    <table id="data_table"/>
                </div>
            );
        }
}

export default ExpertBackground;
