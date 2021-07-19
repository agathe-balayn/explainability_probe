import React, {useEffect, useState} from 'react';
import axios from "axios";
import "../css/RunAlgorithm.less"
import {add_data_url, add_image_url} from "../API";
import {Collapse} from "antd";
const {Panel} = Collapse;

export default function SubmitData(props) {

    const userName = sessionStorage.user.split('"')[5]
    const [ability, setAbility] = useState(true)
    const [userCount, setUserCount] = useState(0)
    const [userInputs, setUserInputs] = useState([])
    const [dataSetName, setDataSetName] = useState("")
    const [dataSet, setDataSet] = useState("")
    const [annotations, setAnnotations] = useState("")
    const [images, setImages] = useState("")
    const [userNames, setUserNames] = useState([])
    const [imagesText, setImagesText] = useState({})
    const [submit, setSubmit] = useState(false)
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );
    useEffect(() => {
        if(submit) {
            addData()
        }
    }, [userNames, images, dataSet, dataSetName, annotations, submit] );


    function addUser() {

        const inputs = []
        if (userCount == 0) {
            setAbility(false)
        }
        for(let i = 0; i < userCount + 1; i++) {

            inputs.push({view: (<p className="inputP">
                                    <input className="textInput" type="text" id={i+1} placeholder="give user name" onChange={(event) => userNames[event.target.id] = event.target.value}></input>
                                </p>)})
        }

        setUserCount(userCount + 1)
        setUserInputs(inputs)
    }
    function removeUser() {
        if (userCount == 1) {
            setAbility(true)
        }
        for (let i = userCount+1; i < userNames.length; i++) {
            userNames.pop()
        }
        const inputs = []

        for(let i = 0; i < userCount - 1; i++) {
            inputs.push({view: (<p className="inputP">
                                    <input className="textInput" type="text" id={i+1} placeholder="give user name" onChange={(event) => {
                                    userNames[event.target.id] = event.target.value
                                    }}></input>
                                </p>)})
        }

        setUserCount(userCount - 1)
        setUserInputs(inputs)
    }

    /**
     * Submits data to the backend, to multiple API endpoints:
     * /api/SECAAlgo/add_data/ For the chosen .csv and .json file
     * /api/SECAAlgo/add_image/ For the images
     */
    function addData() {
        const errors = document.getElementsByClassName("errorDiv")[0]
        errors.innerHTML = ""
        setSubmit(false)
        var data_success = false
        var image_success = false


        if (dataSetName === "") {
            const error = document.createElement("div")
            error.className = "error"
            error.innerHTML = "Data set name cannot be empty."
            errors.appendChild(error)
        }
        if (dataSetName.includes(" ")) {


            const error = document.createElement("div")
            error.className = "error"
            error.innerHTML = "Data set name cannot include spaces."
            errors.appendChild(error)
        }
        if (images === "" || typeof images === "undefined") {


            const error = document.createElement("div")
            error.className = "error"
            error.innerHTML = "images cannot be empty."
            errors.appendChild(error)
        }
        if (annotations === "" || typeof annotations === "undefined") {


            const error = document.createElement("div")
            error.className = "error"
            error.innerHTML = "annotations cannot be empty."
            errors.appendChild(error)
        }
        if (dataSet === "" || typeof dataSet === "undefined") {


            const error = document.createElement("div")
            error.className = "error"
            error.innerHTML = "Data set cannot be empty."
            errors.appendChild(error)
        }



        for(let i = 0; i < images.length; i++) {
                if(images[i].name.substring(images[i].name.length-3, images[i].name.length) !== "jpg") {

                    const error = document.createElement("div")
                    error.className = "error"
                    error.innerHTML = "One or more images have an invalid format."
                    errors.appendChild(error)

                    break
                }
        }
        if (errors.children.length < 1) {

            function submitImages (imageList, textList, i) {

                const imageReader = new FileReader();

                imageReader.onload = function(event) {

                     textList[imageList[i].name] = imageReader.result

                     if (i+1 == imageList.length) {
                        try {

                            axios
                                .post(
                                    add_image_url,
                                    {
                                          "image_data":  textList,
                                          "dataset_name": dataSetName
                                    },
                                    {
                                        headers: {
                                            "Content-Type": "application/json" ,
                                            Authorization: "Token " + token
                                        }

                                    }
                                )
                                .then(response => {
                                   if(data_success) {
                                        const success = document.createElement("div")
                                        success.className = "success"
                                        success.innerHTML = "Data added successfully."
                                        errors.appendChild(success)
                                   }
                                   else {
                                        image_success = true;
                                   }
                                }
                                )
                                .catch(function (exception) {
                                        const error = document.createElement("div")
                                        error.className = "error"
                                        error.innerHTML = "Something went wrong with processing the images. Try again later."
                                        errors.appendChild(error)
                                }
                            );
                        }
                        catch(exception) {
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the images. Check if the files are in order and try again later."
                            errors.appendChild(error)

                        }
                     }
                     else {
                        submitImages (imageList, textList, i + 1)
                     }
                }
                imageReader.readAsDataURL(imageList[i]);

            }
            
            //Post to the API
            submitImages (images, {}, 0)

            //Interpret json and csv files and post as json to the add_data API
            try {
                const users = [userName]

                for (var u in userNames) {
                    users.push(userNames[u])
                }

                var dataReader = new FileReader();
                dataReader.addEventListener("loadend", function() {

                    const dataSetText = dataReader.result

                    try {
                        var annotationReader = new FileReader();
                        annotationReader.addEventListener("loadend", function() {
                            const annotationsText = annotationReader.result
                            axios
                                .post(
                                    add_data_url,
                                    {
                                          "dataset_name": dataSetName,
                                          "username": users,
                                          "data_set": dataSetText,
                                          "annotations": annotationsText
                                    },
                                    {
                                        headers: {
                                            "Content-Type": "application/json" ,
                                            Authorization: "Token " + token
                                        }

                                    }
                                )
                                .then(response => {
                                    if(image_success) {
                                        const success = document.createElement("div")
                                        success.className = "success"
                                        success.innerHTML = "Data added successfully."
                                        errors.appendChild(success)
                                   }
                                   else {
                                        data_success = true;
                                   }
                               }
                                )
                                .catch(function (e) {
                                        const error = document.createElement("div")
                                        error.className = "error"
                                        error.innerHTML = "Something went wrong with processing the data. Try again later. "
                                        errors.appendChild(error)

                            });
                        })
                        annotationReader.readAsText(annotations);

                    }
                    catch (e) {
                        const error = document.createElement("div")
                        error.className = "error"
                        error.innerHTML = "Invalid annotations. Make sure data is represented in the right format."
                        errors.appendChild(error)
                    }
                })
                dataReader.readAsText(dataSet);

                }
                catch (e) {
                    const error = document.createElement("div")
                    error.className = "error"
                    error.innerHTML = "Invalid prediction set. Make sure data is represented in the right format and correctly structured."
                    errors.appendChild(error)
                }
        }

   }
    return (
        <div className="AddToDataSet">
            <div className="errorDiv">

            </div>
            <div className="main">
                <div className="inputText">
                    <p className="inputP"> Name of data set </p>
                    <p className="inputP"> Data set (.csv) </p>
                    <p className="inputP"> Annotation (.json)  </p>
                    <p className="inputP"> All the images (.jpeg) </p>
                    <p className="inputP"> Additional Users <br></br> You will automatically be <br></br> assigned to this project.</p>
                </div>

                <div className="mid">
                    <p className="inputP"> <input className="dataSetName" type="text" placeholder="give name for set" onChange={(event) => setDataSetName(event.target.value) }></input></p>
                    <p className="inputP"> <input className="dataSet" type="file" accept=".csv" onChange={(event) => setDataSet(event.target.files[0])}></input></p>
                    <p className="inputP"> <input className="annotations" type="file" accept=".json" onChange={(event) => setAnnotations(event.target.files[0])}></input></p>
                    <p className="inputP"> <input className="images" type="file" onChange={(event) => {setImages(event.target.files)}
                    } multiple></input></p>
                    <div>
                        <p className="inputP"> <input className="textInput" id="0" type="text" placeholder="give user name" onChange={(event) => {userNames[event.target.id] = event.target.value}}></input> <button className ="buttonAssignUser" onClick={addUser}> + </button> <button className ="buttonAssignUser" disabled={ability} onClick={removeUser}> - </button></p>
                        {userInputs.map(item =>
                            item.view
                        )}
                    </div>
                    <p><button className="buttonSubmit" onClick={
                   () => {
                        setSubmit(true)
                        addData()
                    }

                    }>Submit</button></p>
                </div>
                <div className="mid">
                    <div className="data_set">
                        <Collapse>
                            <Panel header="Example for data set">
                                {
                                "The data set should be a csv file with three columns,\n"
                                + "with the titles image_name, category, predicted.\n"
                                + "The first column should consist of the names of images.\n"
                                + "The second column should consist of the names of the actual class of the image.\n"
                                + "The third column should consist of the names of the predicted class of the image.\n"

                                }
                                <table>
                                  <tr>
                                    <th>image_name</th>
                                    <th>category</th>
                                    <th>predicted</th>
                                  </tr>
                                  <tr>
                                    <td>picture_of_cat.jpg</td>
                                    <td>cat</td>
                                    <td>dog</td>
                                  </tr>
                                  <tr>
                                    <td>picture_of_bird.jpg</td>
                                    <td>bird</td>
                                    <td>bird</td>
                                  </tr>
                                </table>
                            </Panel>
                        </Collapse>
                    </div>
                    <br>
                    </br>
                    <div className="annotations">
                        <Collapse>
                            <Panel header="Example for annotations">
                                {"The annotations should be a json file consisting of a single array of json object of the following format:"}<br></br>
                                {"{"}<br></br>
                                 {"    'pid': [int],"} <br></br>
                                 {"    'category_id': [int],"} <br></br>
                                 {"    'object1_label': [string],"}<br></br>
                                 {"    'object1_bbox': [String],"}<br></br>
                                 {"    'object1_score':[int],"}<br></br>
                                 {"    'object2_label': [string],"}<br></br>
                                 {"    'object2_bbox': [string],"}<br></br>
                                 {"    'object2_score': [int],"}<br></br>
                                 {"    'relation_label': [string],"}<br></br>
                                 {"    'relation_score': [int],"}<br></br>
                                 {"    'weight': [int],"}<br></br>
                                 {"    'session_id': [int],"}<br></br>
                                 {"    'valid': [boolean],"}<br></br>
                                 {"    'is_typical': [boolean],"}<br></br>
                                 {"    'reason': [string],"}<br></br>
                                 {"    'is_annotated': [boolean],"}<br></br>
                                 {"    'is_chosen': [boolean],"}<br></br>
                                 {"    'image_name': [string],"}<br></br>
                                 {"    'heatmap_name': [string]"}<br></br>
                                 {'}'}<br></br>
                            </Panel>
                        </Collapse>
                    </div>
                </div>
            </div>
        </div>
    );
}
