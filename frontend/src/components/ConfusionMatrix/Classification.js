import React, {useEffect, useState} from 'react';
import { Pie } from 'react-chartjs-2';
import { Button, Radio } from "antd";
import { Link } from "react-router-dom";
import axios from "axios";
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
    let [ruleTypicality, setRuleTypicality] = useState([]);
    let [conceptTypicality, setConceptTypicality] = useState([]);
    const [matrixImages, setMatrixImages] = useState([])
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );

    // Randomly decide the category's color for the charts
    let total_images = 0
    for (let i = 0; i < comprehensiveView.length; i++) {
        const rand = 'rgb(' + Math.floor(Math.random() * 256) + ', ' + Math.floor(Math.random() * 256) + ', '
            + Math.floor(Math.random() * 256) +  ')';
        colors[i] = rand;
        total_images += comprehensiveView[i]
    }
    console.log(total_images)
    let fraction_images = []
    for (let i = 0; i < comprehensiveView.length; i++) {
        fraction_images.push((comprehensiveView[i] / total_images).toFixed(2))
    }
    console.log(fraction_images)


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
                      "session_id": session_id[0]
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
            typicality: conceptTypicality[key]['typicality']
        });
    }

    const rule_data = [];
    for (let key in ruleTypicality) {
        let innerArray = [];
        for (let innerKey in ruleTypicality[key]) {
            innerArray.push({
                concept: (key) + " -> " + innerKey,
                percentage_present: ruleTypicality[key][innerKey]['percent_present'],
                percentage_correct: ruleTypicality[key][innerKey]['percent_correct'],
                typicality: ruleTypicality[key][innerKey]['typicality']
            });
        }
        rule_data.push({
            concept: key,
            innerArray: innerArray
        });
    }

    sort(concept_data, sorting);

    const size = 400;
    const concept_data_view = [];
    for (let i = 0; i < concept_data.length; i++) {
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
                            </div>

                            <div className="restBar"
                                 style={{width: (size * (1 - (concept_data[i].percentage_present ))).toString() + "px", backgroundColor: "#D3D3D3", float: "left"}}>
                                 {((concept_data[i].percentage_present) * 100).toFixed(2).toString() + "%"}
                            </div>
                        </div>
                        
                        
                        <br>
                        </br>
                    </div>
        })
    }
    const rule_data_view = [];
    sort(rule_data, sorting);
    for (let i = 0; i < rule_data.length; i++) {
        for (let e = 0; e < rule_data[i].innerArray.length; e++) {
            rule_data_view.push({
                view:
                    <div className={"ruleRow" + (i%2).toString()}>
                            <h5>
                                {rule_data[i].innerArray[e].concept}
                            </h5>
                            <div className="totalBar">
                                <div className="typicality" style={{width: (size * rule_data[i].innerArray[e].typicality).toFixed(2).toString() + "px", maxWidth: (size * 0.7).toString() + "px"}}></div>
                                <div className="typicalityText">typicality: {rule_data[i].innerArray[e].typicality.toFixed(2)}</div>
                            </div>

                            <div>
                                <div className="ruleCorrectBar" style={{width: (size * rule_data[i].innerArray[e].percentage_correct * rule_data[i].innerArray[e].percentage_present).toString() + "px", backgroundColor: "#7CFC00"}}>
                                {(rule_data[i].innerArray[e].percentage_correct * 100).toFixed(2).toString() + "%"}
                                </div>

                                <div className="ruleInCorrectBar" style={{width: (size * (rule_data[i].innerArray[e].percentage_present - rule_data[i].innerArray[e].percentage_correct * rule_data[i].innerArray[e].percentage_present)).toString() + "px", backgroundColor: "#FF0000"}}>
                                </div>

                                <div className="restBar" style={{width: (size * (1 - (rule_data[i].innerArray[e].percentage_present))).toString() + "px", backgroundColor: "#D3D3D3", float: "left"}}>
                                {(rule_data[i].innerArray[e].percentage_present * 100).toFixed(2).toString() + "%"}
                                </div>
                            </div>
                            
                            <br>
                            </br>
                        </div>
            })
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
        for (let image in matrixImages[key]["images"]) {
            images.push({
                view:
                    <div>
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
                                <Radio value={"percentage_correct"}>Percentage of correct classification</Radio><br/>
                            </RadioGroup>
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
                    </div>

                    <div className={"left-of-charts"} style={{"minHeight": (800).toString() + "px"}}>
                        <div className={"main-wrap"}>
                            <div className={"left"}>
                                <h2>Significant concepts in the images within this binary task</h2>
                                <div className={"main-wrap"}>
                                    <p style={{color:"#32CD32"}}>Percentage of correct predictions among concept-associated images</p>
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
                                    <p style={{color:"#32CD32"}}>Percentage of correctly classified images within rule-associated images</p>
                                    <p style={{color:"#556B2F"}}>Percentage of concept-associated images among images with the predicted class</p>
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
        </div>
    );
}
