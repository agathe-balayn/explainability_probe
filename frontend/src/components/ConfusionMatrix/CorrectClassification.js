import React, {useEffect, useState} from 'react';
import { Link } from "react-router-dom";
import { Button } from "antd";
import axios from "axios";
import { matrix_images as matrix_images_url, binary_query as binary_query_url } from "../../API";
import "../../css/CorrectClassification.less";

export default function CorrectClassification(props) {

    const data  = props.location.state;
    const comprehensiveLabel = data[0];
    const binaryLabel = data[1];
    const comprehensiveView = data[2];
    const binaryView = data[3];
    const binaryMatrixClasses = data[4];

    let [ruleTypicality, setRuleTypicality] = useState([]);
    let [conceptTypicality, setConceptTypicality] = useState([]);
    const [matrixImages, setMatrixImages] = useState([])
    const session_id = useState(JSON.parse(sessionStorage.getItem("problem")))
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );

    const getScores = (event) => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];

        axios
            .post(
                binary_query_url,
                {
                    "query_type": "rules",
                    "image_setting": "binary_matrix",
                    "add_class": [binaryMatrixClasses[0], binaryMatrixClasses[1]],
                    "session_id": session_id[0]
                },
                {
                    headers: {
                        "Content-Type": "application/json" ,
                        Authorization: "Token " + token
                    }
                }
            )
            .then(response => {
                    setConceptTypicality(response.data['concepts']);
                    setRuleTypicality(response.data['rules']);
                }
            )
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
                        "Content-Type": "application/json" ,
                        Authorization: "Token " + token,
                    }
                }
            )
            .then(response => {
                setMatrixImages(response.data)
            })
        .catch(function (error) {
            const e = document.createElement("div")
            e.innerHTML = "Something went wrong when retrieving the images. Try again later."
            e.className = "error"
            errorDiv.appendChild(e)
        });
    }

    // Retrieve them ONLY at the first load of the page because [0].
    useEffect(() => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        errorDiv.innerHTML = ""
        getScores();
        getMatrixImages();
    }, [0] );

    let concept_data = [];
    for (let key in conceptTypicality) {
        concept_data.push({
            concept: key,
            percentage_present: conceptTypicality[key]['percent_present'],
            percentage_correct: conceptTypicality[key]['percent_correct'] * conceptTypicality[key]['percent_present'],
            typicality: conceptTypicality[key]['typicality']
        });
    }

    const rule_data = [];
    for (let key in ruleTypicality) {
        let innerArray = [];
        for (let innerKey in ruleTypicality[key]) {
            innerArray.push({
                concept: innerKey,
                percentage_present: ruleTypicality[key][innerKey]['percent_present'],
                percentage_correct: ruleTypicality[key][innerKey]['percent_correct'] * ruleTypicality[key][innerKey]['percent_present'],
                typicality: ruleTypicality[key][innerKey]['typicality']
            });
        }
        rule_data.push({
            concept: key,
            innerArray: innerArray
        });
    }


    const size = 475;
    const concept_data_view = [];
    for (let i = 0; i < concept_data.length; i++) {
        concept_data_view.push({
            view:
                <div className={"conceptRow" + (i%2).toString()}>
                <h5>{concept_data[i].concept}</h5>
                    <div className="totalBar">
                        <div className="typicality" style={{width: (size * concept_data[i].typicality).toString() + "px"}}></div>
                        <div className="typicalityText">typicality: {concept_data[i].typicality}</div>
                    </div>

                    <div>
                        <div className="conceptCorrectBar" style={{width: (size * concept_data[i].percentage_correct).toString() + "px"}}>
                            {(concept_data[i].percentage_correct * 100).toFixed(2).toString() + "%"}
                        </div>

                        <div className="conceptIncorrectBar" style={{width: (size * (concept_data[i].percentage_present - concept_data[i].percentage_correct)).toString() + "px"}}></div>
                        <div className="restBar" style={{width: (size * (1 - (concept_data[i].percentage_present + concept_data[i].percentage_correct))).toString() + "px"}}></div>
                    </div>
                    <br></br>
                    <div>
                        <div className="percentageOfTotalBar" style={{width: (size * concept_data[i].percentage_present).toString() + "px"}}>
                            {((concept_data[i].percentage_correct + concept_data[i].percentage_present) * 100).toFixed(2).toString() + "%"}</div>
                        <div className="pointer"></div>
                    </div>
                    <br></br>
                </div>
        })
    }

    const rule_data_view = [];
    for (let i = 0; i < rule_data.length; i++) {
        for (let e = 0; e < rule_data[i].innerArray.length; e++) {
            rule_data_view.push({
                view:
                    <div className={"ruleRow" + (i%2).toString()}>
                        <h5>{rule_data[i].concept + " -> " + rule_data[i].innerArray[e].concept}</h5>
                        <div className="totalBar">
                            <div className="typicality" style={{width: (size * rule_data[i].innerArray[e].typicality).toFixed(2).toString() + "px", maxWidth: (size * 0.7).toString() + "px"}}></div>
                            <div className="typicalityText">typicality: {rule_data[i].innerArray[e].typicality.toFixed(2)}</div>
                        </div>

                        <div>
                            <div className="ruleCorrectBar" style={{width: (size * rule_data[i].innerArray[e].percentage_correct).toString() + "px"}}></div>
                            <div className="ruleInCorrectBar" style={{width: (size * (rule_data[i].innerArray[e].percentage_present - rule_data[i].innerArray[e].percentage_correct)).toString() + "px"}}></div>

                            <div className="restBar" style={{width: (size * (1 - (rule_data[i].innerArray[e].percentage_present + rule_data[i].innerArray[e].percentage_correct))).toString() + "px"}}></div>
                        </div>
                        <br></br>
                        <div>
                            <div className="percentageOfTotalBar" style={{width: (size * rule_data[i].innerArray[e].percentage_present).toString() + "px"}}>
                                {(rule_data[i].innerArray[e].percentage_present * 100).toFixed(2).toString() + "%"}</div>
                            <div className="pointer"></div>
                        </div>
                        <br></br>
                    </div>
            })
        }
    }

    const columns = []
    let height = 0;
    for (let key in matrixImages) {
        if (height < matrixImages[key]["images"].length) {
            height = matrixImages[key]["images"].length
        }
    }
    for (let key in matrixImages) {
        const images = []

        for(let image in matrixImages[key]["images"]) {
            images.push({
                view:
                    <div>
                        <img className="matrixImage" src={'data:image/jpeg;base64,' + matrixImages[key]["heatmaps"][image]}></img>
                        <img className="matrixImage" src={'data:image/jpeg;base64,' + matrixImages[key]["images"][image]}></img>
                    </div>
            })
        }

        columns.push({
            view:
                <div className={"imageColumn"} style={{"width":"1450px"}}>
                    <h3 className={"imageColumnTitle"}>{"Images"}</h3>
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
                <div className="upper-section">
                    <div className={"text"}>
                        <div className={"main-wrap"}>
                            <div className={"left"}>
                                <h2>Significant concepts in the images within this binary task</h2>
                                <h4>Legend:</h4>
                                <div className={"main-wrap"}>
                                    <p id={"conceptP1"}>Percentage of correct predictions among concept-associated images</p>
                                    <p id={"conceptP2"}>Percentage of concept-associated images in dataset</p>
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
                                    <p id={"ruleP1"}>Percentage of correctly classified images within rule-associated images</p>
                                    <p id={"ruleP2"}>Percentage of concept-associated images among images with the predicted class</p>
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
        </div>
    );
}
