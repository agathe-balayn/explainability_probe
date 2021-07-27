import React, {useEffect, useState} from 'react';
import { Pie } from 'react-chartjs-2';
import { Button, Radio } from "antd";
import { Link } from "react-router-dom";
import axios from "axios";
import Modal from 'react-bootstrap/Modal'
import { matrix_images as matrix_images_url, binary_query as binary_query_url } from "../../API";
import "../../css/Classification.less"
const RadioGroup = Radio.Group;

export default function Classification(props) {

    const data  = props.location.state; // sent from the Confusion Matrix
    const comprehensiveLabel = data[0];
    const binaryLabel = data[1];
    console.log(data)
    const comprehensiveView = data[2];
    const binaryView = data[2];
    const binaryMatrixClasses = data[1];
    const session_id = useState(JSON.parse(sessionStorage.getItem("session")))
    let colors = []; // for the charts

    let [sorting, setSorting] = useState("concept");
    let [filtering, setFiltering] = useState("all");
    let [settingClasses, setSettingClasses] = useState("binary");
    let [ruleTypicality, setRuleTypicality] = useState([]);
    let [conceptTypicality, setConceptTypicality] = useState([]);
    const [matrixImages, setMatrixImages] = useState([])
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState([]);

    // Randomly decide the category's color for the charts
    let total_images = 0
    for (let i = 0; i < comprehensiveView.length; i++) {
        const rand = 'rgb(' + Math.floor(Math.random() * 256) + ', ' + Math.floor(Math.random() * 256) + ', '
            + Math.floor(Math.random() * 256) +  ')';
        colors[i] = rand;
        total_images += comprehensiveView[i]
    }
    let fraction_images = []
    for (let i = 0; i < comprehensiveView.length; i++) {
        fraction_images.push((comprehensiveView[i] / total_images).toFixed(2))
    }


    // Inputs for charts

    const comprehensiveData = {
        labels: comprehensiveLabel,
        datasets: [{
            label: 'Comprehensive overview',
            data: fraction_images,
            backgroundColor: colors,
            hoverOffset: 4,
        }]
    };
    let list_labels = []
    if (settingClasses == "binary"){
        list_labels = [binaryLabel[0], binaryLabel[1]]
    }else{
        list_labels = [ "correctly predicted " +  binaryLabel[0], "correctly predicted " +  binaryLabel[1],  "incorrectly predicted " +  binaryLabel[0], "incorrectly predicted " +  binaryLabel[1]]
    }
    const binaryData = {
        labels: [binaryLabel[0] + " predicted as " + binaryLabel[1], binaryLabel[1] + " predicted as " + binaryLabel[0], "correctly predicted " +  binaryLabel[0], "correctly predicted " +  binaryLabel[1]],
        datasets: [{
            label: 'Strict binary classification',
            data: fraction_images,
            backgroundColor: [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
                'rgb(255, 205, 86)',
                'rgb(0, 200, 86)'
            ],
            hoverOffset: 4,
        }]
    };

    const getScores = (event) => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        axios
            .post(
                binary_query_url,
                {
                      "query_type": "rules",
                      "image_setting": "binary_matrix",
                      "add_class": [binaryMatrixClasses[0], binaryMatrixClasses[1]],
                      "session_id": session_id[0],
                      "task_type":settingClasses
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "Token " + token,
                    }
                }

            )
            .then(response => {
                setConceptTypicality(response.data['concepts']);
                setRuleTypicality(response.data['rules']);
            })
            .catch(function (error) {

                const e = document.createElement("div")
                e.innerHTML = "Something went wrong when retrieving the typicality scores. Try again later."
                e.className = "error"
                errorDiv.appendChild(e)

                setConceptTypicality([]);
                setRuleTypicality([]);
            });
    };

    const getMatrixImages = (event) => {

        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        axios
            .get(
                matrix_images_url,
                {
                    params: {
                        "classA": binaryMatrixClasses[0],
                        "classB": binaryMatrixClasses[1],
                        "session_id": session_id[0]
                    },
                    headers: {
                        Authorization: "Token " + token
                    }
                }
            )
        .then(response => {
               setMatrixImages(response.data)
             }
        )
        .catch(function (error) {

            const e = document.createElement("div")
            e.innerHTML = "Something went wrong when retrieving the images. Try again later."
            e.className = "error"
            errorDiv.appendChild(e)

        });
    }


    // Function that sorts the entries in the fetched data.
    function sort(array, on) {
        
        for (let i = 0; i < array.length; i++) {
            var min_idx = i;
            for (let j = i + 1; j < array.length; j++) {
                if (array[j][on] > array[min_idx][on]) {
                    min_idx = j;
                }
            }
            [array[min_idx], array[i]] = [array[i], array[min_idx]]
        }
        return array
    }


    // Retrieve them at the first load of the page because of [0].
    useEffect(() => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        errorDiv.innerHTML = ""

        getScores();
        getMatrixImages();
    }, [0] );

    const concept_data = []
    for (let key in conceptTypicality) {
        concept_data.push({
            concept: key,
            percentage_present: conceptTypicality[key]['percent_present'],
            percentage_correct: conceptTypicality[key]['percent_correct'],
            typicality: conceptTypicality[key]['typicality'],
            percentage_incorrect: 1 -conceptTypicality[key]['percent_correct'],
            class_presence: conceptTypicality[key]['class_presence']
        });
    }

    const fillModalData = ( heatmap, image, annotations,gt,label,confidence) => {
        setModalData({
            "image": image,
            "heatmap": heatmap,
            "annotations" : annotations,
            "gt": gt,
            "label": label,
            "confidence": confidence
        });
        setShowModal(true);
    }

    
    const rule_data = [];
    for (let key in ruleTypicality) {
        
        for (let innerKey in ruleTypicality[key]) {
            //let innerArray = [];
            rule_data.push({
                concept: (key) + " -> " + innerKey,
                percentage_present: ruleTypicality[key][innerKey]['percent_present'],
                percentage_correct: ruleTypicality[key][innerKey]['percent_correct'],
                typicality: ruleTypicality[key][innerKey]['typicality'],
                percentage_incorrect: 1 - ruleTypicality[key][innerKey]['percent_correct'],
            });
            //rule_data.push({
            //concept: key,
            //innerArray: innerArray
        //});
        }
        
    }
    




    // Function that sorts the entries in the fetched data.
    function filter_concept(array, on) {
        console.log("i am filtering on")
        console.log(on)
        const concept_data = []
        for (let key in conceptTypicality) {
            if (on == "all"){
                concept_data.push({
                    concept: key,
                    percentage_present: conceptTypicality[key]['percent_present'],
                    percentage_correct: conceptTypicality[key]['percent_correct'],
                    typicality: conceptTypicality[key]['typicality'],
                    percentage_incorrect: 1 -conceptTypicality[key]['percent_correct'],
                    class_presence: conceptTypicality[key]['class_presence']
                });
            }else if (on == "cooccuring"){
                let nb_more_than_zero = 0
                for (let i in conceptTypicality[key]['class_presence']){
                    if (conceptTypicality[key]['class_presence'][i] > 0){
                        nb_more_than_zero += 1
                    }
                }
                if (nb_more_than_zero > 1){
                       concept_data.push({
                        concept: key,
                        percentage_present: conceptTypicality[key]['percent_present'],
                        percentage_correct: conceptTypicality[key]['percent_correct'],
                        typicality: conceptTypicality[key]['typicality'],
                        percentage_incorrect: 1 -conceptTypicality[key]['percent_correct'],
                        class_presence: conceptTypicality[key]['class_presence']
                    }); 
                }
                

            }else{
                if (conceptTypicality[key]['class_presence']["presence_among_" + on] > 0){
                    concept_data.push({
                        concept: key,
                        percentage_present: conceptTypicality[key]['percent_present'],
                        percentage_correct: conceptTypicality[key]['percent_correct'],
                        typicality: conceptTypicality[key]['typicality'],
                        percentage_incorrect: 1 -conceptTypicality[key]['percent_correct'],
                        class_presence: conceptTypicality[key]['class_presence']
                    }); 
                }

            }
        }
        console.log("new data")
        console.log(concept_data)
        return concept_data
    }

    sort(concept_data, sorting);
    filter_concept(concept_data, filtering);

    const size = 400;
    const concept_data_view = [];
    if (settingClasses == "binary"){
        for (let i = 0; i < concept_data.length; i++) {
            let class_presence_string = ""
            for (let j in concept_data[i].class_presence) {
                class_presence_string += ("(" +  j +": " + (concept_data[i].class_presence[j] * 100).toFixed(2) + "%) ").toString() 
            }
            concept_data_view.push({
                view:
                    <div className={"conceptRow" + (i % 2).toString()}>
                            <h5>
                                {concept_data[i].concept}
                            </h5>
                            <div className="totalBar">
                                <div className="typicality" style={{width: (size * concept_data[i].typicality).toString() + "px"}}/>
                                <div className="typicalityText">typicality: {concept_data[i].typicality}</div>
                            </div>

                            <div>
                                <div className="conceptCorrectBar"
                                     style={{width: (size * concept_data[i].percentage_correct * concept_data[i].percentage_present).toString() + "px", backgroundColor: "#7CFC00"}}>
                                    {(concept_data[i].percentage_correct * 100).toFixed(2).toString() + "%"}
                                </div>

                                <div className="conceptIncorrectBar"
                                     style={{width: (size * (concept_data[i].percentage_present - concept_data[i].percentage_correct * concept_data[i].percentage_present)).toString() + "px", backgroundColor: "#FF0000"}}>
                                     {(concept_data[i].percentage_incorrect * 100).toFixed(2).toString() + "%"}
                                </div>

                                <div className="restBar"
                                     style={{width: (size * (1 - (concept_data[i].percentage_present ))).toString() + "px", backgroundColor: "#D3D3D3", float: "left"}}>
                                     {((concept_data[i].percentage_present) * 100).toFixed(2).toString() + "%"}
                                </div>
                            </div><br></br>
                            <div>{class_presence_string}

                            </div>
                            
                            
                            <br>
                            </br>
                        </div>
            })
        }
    }else{
        for (let i = 0; i < concept_data.length; i++) {
            let class_presence_string = ""
            for (let j in concept_data[i].class_presence) {
                class_presence_string += ("(" +  j +": " + (concept_data[i].class_presence[j] *100).toFixed(2)+ "%) ").toString() 
            }
            concept_data_view.push({
                view:
                    <div className={"conceptRow" + (i % 2).toString()}>
                            <h5>
                                {concept_data[i].concept}
                            </h5>
                            <div className="totalBar">
                                <div className="typicality" style={{width: (size * concept_data[i].typicality).toString() + "px"}}/>
                                <div className="typicalityText">typicality: {concept_data[i].typicality}</div>
                            </div>

                            <div>
                                

                                <div className="restBar"
                                     style={{width: (size * ((concept_data[i].percentage_present ))).toString() + "px", backgroundColor: "#D3D3D3", float: "left"}}>
                                     {((concept_data[i].percentage_present) * 100).toFixed(2).toString() + "%"}
                                </div>
                            </div><br></br>
                            <div>{class_presence_string}

                            </div>
                            
                            
                            <br>
                            </br>
                        </div>
            })
        }
    }
    const rule_data_view = [];
    sort(rule_data, sorting);

    if (settingClasses == "binary"){
        for (let i = 0; i < rule_data.length; i++) {
            //for (let e = 0; e < rule_data[i].innerArray.length; e++) {
                rule_data_view.push({
                    view:
                        <div className={"ruleRow" + (i%2).toString()}>
                                <h5>
                                    {rule_data[i].concept}
                                </h5>
                                <div className="totalBar">
                                    <div className="typicality" style={{width: (size * rule_data[i].typicality).toFixed(2).toString() + "px", maxWidth: (size * 0.7).toString() + "px"}}></div>
                                    <div className="typicalityText">typicality: {rule_data[i].typicality.toFixed(2)}</div>
                                </div>

                                <div>
                                    <div className="ruleCorrectBar" style={{width: (size * rule_data[i].percentage_correct * rule_data[i].percentage_present).toString() + "px", backgroundColor: "#7CFC00"}}>
                                    {(rule_data[i].percentage_correct * 100).toFixed(2).toString() + "%"}
                                    </div>

                                    <div className="ruleInCorrectBar" style={{width: (size * (rule_data[i].percentage_present - rule_data[i].percentage_correct * rule_data[i].percentage_present)).toString() + "px", backgroundColor: "#FF0000"}}>
                                    {(rule_data[i].percentage_incorrect * 100).toFixed(2).toString() + "%"}
                                    </div>

                                    <div className="restBar" style={{width: (size * (1 - (rule_data[i].percentage_present))).toString() + "px", backgroundColor: "#D3D3D3", float: "left"}}>
                                    {(rule_data[i].percentage_present * 100).toFixed(2).toString() + "%"}
                                    </div>
                                </div>
                                
                                <br>
                                </br>
                            </div>
                })
            //}
        }
    }else{
        for (let i = 0; i < rule_data.length; i++) {
            //for (let e = 0; e < rule_data[i].innerArray.length; e++) {
                rule_data_view.push({
                    view:
                        <div className={"ruleRow" + (i%2).toString()}>
                                <h5>
                                    {rule_data[i].concept}
                                </h5>
                                <div className="totalBar">
                                    <div className="typicality" style={{width: (size * rule_data[i].typicality).toFixed(2).toString() + "px", maxWidth: (size * 0.7).toString() + "px"}}></div>
                                    <div className="typicalityText">typicality: {rule_data[i].typicality.toFixed(2)}</div>
                                </div>

                                <div>
                                    

                                    <div className="restBar" style={{width: (size * ((rule_data[i].percentage_present))).toString() + "px", backgroundColor: "#D3D3D3", float: "left"}}>
                                    {(rule_data[i].percentage_present * 100).toFixed(2).toString() + "%"}
                                    </div>
                                </div>
                                
                                <br>
                                </br>
                            </div>
                })
            //}
        }
    }

    const columns = []
    let height = 0;
    let titleChar = 0;
    for (let key in matrixImages) {
        if (height < matrixImages[key]["images"].length) {
            height = matrixImages[key]["images"].length
        }
        if (titleChar < key.length) {
            titleChar = key.length
        }
    }
    for (let key in matrixImages) {
        const images = []
        const [gt, label] = key.replace("_classified_as_"," ").split(" ");
        for (let image in matrixImages[key]["images"]) {
            images.push({
                view:
                <div className="hover-click-pair d-flex align-items-center" onClick={() => 
                    fillModalData(
                        matrixImages[key]["heatmaps"][image],
                        matrixImages[key]["images"][image],
                        matrixImages[key]["annotations"][image],
                        gt,
                        label, 
                        matrixImages[key]["confidence"][image] 
                        ) }>
                        <img className="matrixImage"
                           src={'data:image/jpeg;base64,' + matrixImages[key]["heatmaps"][image]}></img>
                        <img className="matrixImage"
                           src={'data:image/jpeg;base64,' + matrixImages[key]["images"][image]}></img>
                    </div>
            })
        }

        columns.push({
            view:
                <div className={"imageColumn"}
                    style={{"height": (height * 150 + 50 + Math.floor(titleChar / 45) * 20 + 20).toString() + "px"}}>

                    <h3 className={"imageColumnTitle"}
                        style={{"marginBottom": ((Math.floor(key.length / 45) - Math.floor(titleChar / 45)) * -20).toString() + "px"}}>{key.replace(/_/g, " ")}</h3>
                    {
                        images.map(item => (
                            <>
                                {item.view}
                            </>
                        ))
                    }
                </div>
        })
    }
    const fetchData = (event) => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        axios
            .post(
                binary_query_url,
                {
                      "query_type": "rules",
                      "image_setting": "binary_matrix",
                      "add_class": [binaryMatrixClasses[0], binaryMatrixClasses[1]],
                      "session_id": session_id[0],
                      "task_type":settingClasses
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "Token " + token,
                    }
                }

            )
            .then(response => {
                console.log("collected data")
                setConceptTypicality(response.data['concepts']);
                setRuleTypicality(response.data['rules']);
            })
            .catch(function (error) {
                console.log("data not found")

                const e = document.createElement("div")
                e.innerHTML = "Something went wrong when retrieving the typicality scores. Try again later."
                e.className = "error"
                errorDiv.appendChild(e)

                setConceptTypicality([]);
                setRuleTypicality([]);
            });
    }

return (
    <div>
        <div className="backHeader">
            <Link className={"link"} to={{pathname: "/home?tab=3"}}>
                <Button className="backButton">Back</Button>
            </Link>
        </div>
        <div className="errorDiv">
        </div>

        <div className={"everything"}>
            <div>
                <div className={"chart"}>
                    <div className="sort">
                        <div className="subtitle"><h1>Order of representation</h1></div>
                        <RadioGroup value={sorting} onChange={(event) => {
                            setSorting(event.target.value);
                            sort(concept_data, sorting);
                            sort(rule_data, sorting);
                        }}>
                            <Radio value={"concept"}>Alphabetical order</Radio><br/>
                            <Radio value={"typicality"}>Typicality</Radio><br/>
                            <Radio value={"percentage_correct"}>Percentage of correct predictions</Radio><br/>
                            <Radio value={"percentage_present"}>Percentage of concept-associated images</Radio><br/>
                        </RadioGroup>
                    </div>
                    <div className="sort">
                        <div className="subtitle"><h1>Settings</h1></div>
                        <RadioGroup value={settingClasses} onChange={(event) => {
                            setSettingClasses(event.target.value);
                            

                            
                        }}>
                            <Radio value={"binary"}>Binary task</Radio><br/>
                            <Radio value={"4task"}>Distinction between correct and incorrect predictions (4-class task)</Radio><br/>
                        </RadioGroup>
                        <Button onClick={fetchData}>Search</Button>
                    </div>
                    
                    <Pie
                        data={{
                            labels: binaryData.labels,
                            datasets: binaryData.datasets
                        }}
                        options = {{
                            radius: "70%",
                            maintainAspectRatio: true,
                        }}
                    />
                    <p>Total images: {total_images}</p>
                    <div className="sort">
                        <div className="subtitle"><h1>Select information to view</h1></div>
                        <RadioGroup value={filtering} onChange={(event) => {
                            console.log("change in filters")
                            console.log(event.target.value)
                            setFiltering(event.target.value);
                            filter_concept(concept_data, event.target.value);
                        }}>
                            <Radio value={"all"}>All</Radio><br/>
                            <Radio value={"cooccuring"}>Co-occuring across predicted classes</Radio><br/>
                            {list_labels.map(a => <Radio value={a}>{a}</Radio>)}
                            
                        </RadioGroup>
                    </div>

                    

                </div>

                <div className={"left-of-charts"} style={{"minHeight": (800).toString() + "px"}}>
                    <div className={"main-wrap"}>
                        <div className={"left"}>
                            <h2>Significant concepts in the images within this binary task</h2>
                            <div className={"main-wrap"}>
                            {settingClasses == "binary" &&
                            <p style={{color:"#32CD32"}}>Percentage of correct predictions among concept-associated images</p>
                            }
                                <p style={{color:"#556B2F"}}>Percentage of concept-associated images in dataset</p>
                            </div>
                            <hr/>
                            <div>
                                {
                                    concept_data_view.map(item => (
                                        <>
                                            {item.view}
                                        </>
                                    ))
                                }
                            </div>
                        </div>

                        <div className={"right"}>
                            <h2>Significant rules in the images within this binary task</h2>
                            <h4> </h4>
                            <div className={"main-wrap"}>
                            {settingClasses == "binary" &&
                                <p style={{color:"#32CD32"}}>Percentage of correctly classified images within rule-associated images</p>
                            }
                                <p style={{color:"#556B2F"}}>Percentage of rule-associated images in dataset</p>
                            </div>
                            <hr/>
                            <div>
                                {
                                    rule_data_view.map(item => (
                                        <>
                                            {item.view}
                                        </>
                                    ))
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/*Here the images will come */}
            <div className="under-charts">
                {
                    columns.map(item => (
                        <>
                            {item.view}
                        </>
                    ))
                }
            </div>
        </div>
        <Modal size={'xl'} show={showModal} onHide={() => { setShowModal(false) }}      >
            <Modal.Header closeButton closeLabel="close window">
                <h4>Details for image of ground truth {modalData["gt"]}</h4>
            </Modal.Header>
            <Modal.Body>
                <div className="row">
                    <div className="col-12">
                        <p>Classified as: {modalData["label"]} (Confidence: {modalData["confidence"]})</p>
                    </div>
                </div>
                <div className="row">
                    <div className="col d-flex flex-column align-items-center">
                        <img src={'data:image/jpeg;base64,' + modalData["image"]}></img>
                        <p>original image</p>
                    </div>
                    <div className="col d-flex flex-column align-items-center">
                        <img src={'data:image/jpeg;base64,' + modalData["heatmap"]}></img>
                        <p>heatmap</p>
                    </div>
                </div>
                {
                    modalData["annotations"] !== undefined && modalData["annotations"].length > 0 ?
                        <>
                            <h5>Annotated concepts ({modalData["annotations"].length}):</h5>
                            <ul style={{ columns: 3 }}>
                                {modalData["annotations"].map(a => <li>{a}</li>)}
                            </ul>
                        </>
                        :
                        <h5>No annotated concepts for this image</h5>
                }
            </Modal.Body>
        </Modal>
    </div>
    );
}
