import React, { useState, useEffect } from "react";
import axios from "axios";
import { Pie } from "react-chartjs-2";
import {binary_query, f1 as f1_url} from "../API";
import { matrix_images as matrix_images_url } from "../API";
import { matrix_data as matrix_data_url } from "../API";
import {Row, Col, Collapse, Radio} from "antd";
import "./ConfusionMatrix/ConfusionMatrix";
import "./Query/Query";
import "../css/Dashboard.less";
import "./ConfusionMatrix/ConfusionMatrix";
import Modal from 'react-bootstrap/Modal'
import QueryClassificationFormulas from "./Query/QueryClassificationFormulas";
const { Panel } = Collapse;
const RadioGroup = Radio.Group;

// Contains a lot of similar content from the confusion matrix.
// It is duplicated because it contains very small differences
// which block that part from being a separate component.
export default function Dashboard(props) {
    let [relativeData, setRelativeData] = useState([]);
    let [absoluteData, setAbsoluteData] = useState([0, 0]);
    let [totalImages, setTotalImages] = useState(0);
    let [categories, setCategories] = useState([]);
    let [matrixImages, setMatrixImages] = useState([]);
    let [ruleTypicality, setRuleTypicality] = useState([]);
    let [conceptTypicality, setConceptTypicality] = useState([]);
    let [binaryData, setBinaryData] = useState([]);
    let [binaryLabels, setBinaryLabels] = useState([]);
    let [sorting, setSorting] = useState("concept");
    let [f1_scores, setF1_scores] = useState([]);
    //State functions to control the modal overlays
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState([]);
    const session_id = useState(JSON.parse(sessionStorage.getItem("session")))
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );

    const getMatrixData = (event) => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        errors.innerHTML = ""
        axios
            .get(
                matrix_data_url,
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "Token " + token,
                    },
                    params: {"session_id": session_id[0]},

                }
            )
            .then(response => {
                setCategories(response.data['categories']);
                setAbsoluteData(response.data['matrix (absolute)']);
                setRelativeData(response.data['matrix (relative)']);
                setTotalImages(response.data['num_images']);
            })
            .catch(function (error) {

                const e = document.createElement("div")
                e.className = "error"
                e.innerHTML = "Something went wrong when retrieving the Confusion matrix, please try again."
                errors.appendChild(e)

                setRelativeData([]);
                setAbsoluteData([]);
                setCategories([]);
            });
    };
    const getMatrixImages = (row, column) => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        axios
            .get(
                matrix_images_url,
            {
                params: {
                    "classA": categories[row],
                    "classB": categories[column],
                    "session_id": session_id[0]
                },
                headers: {
                    "Content-Type": "application/json" ,
                    Authorization: "Token " + token
                }

            })
            .then(response => {
                console.log(response.data)
                setMatrixImages(response.data)
            })
            .catch(function (error) {
                const e = document.createElement("div")
                e.className = "error"
                e.innerHTML = "Something went wrong when retrieving the images, please try again."
                errors.appendChild(e)
            }
        );
    }
    const getScores = (row, column) => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        axios
            .post(
                binary_query,
                {
                    "query_type": "rules",
                    "image_setting": "binary_matrix",
                    "add_class": [categories[row], categories[column]],
                    "session_id": session_id[0]
                },
                {
                    headers: {
                        "Content-Type": "application/json" ,
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
                e.className = "error"
                e.innerHTML = "Something went wrong when retrieving the typicality scores, please try again."
                errors.appendChild(e)

                setConceptTypicality([]);
                setRuleTypicality([]);
            });
    };
    const getBinaryData = (row, column) => {
        setBinaryData([
            absoluteData[row][column], absoluteData[row][column + 1],
            row < absoluteData.length - 1 ? absoluteData[row + 1][column] :  absoluteData[row - 1][column],
            row < absoluteData.length - 1 ? absoluteData[row + 1][column + 1] : absoluteData[row - 1][column + 1]
        ]);
        setBinaryLabels([categories[column], categories[column + 1],
            categories[row],
            row < absoluteData.length -1 ? categories[row + 1]: categories[row - 1]
        ]);
    }
    const getF1 = () => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        axios
            .post(
                f1_url,
                {
                    "session_id": session_id[0]
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "Token " + token
                    },
                }
            )
            .then(response => {
                setF1_scores(response.data)
            })
            .catch(function (error) {
                const e = document.createElement("div")
                e.className = "error"
                e.innerHTML = "Something went wrong when retrieving the f1 scores, please try again."
                errors.appendChild(e)

                setF1_scores([]);
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


    const chartData = {
        labels: binaryLabels,
        datasets: [{
            label: 'Strict binary classification',
            data: binaryData,
            backgroundColor: [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
                'rgb(255, 205, 86)',
                'rgb(0, 200, 86)'
            ],
            hoverOffset: 4,
        }]
    };


    const concept_data = [];
    for (let key in conceptTypicality) {
        concept_data.push({
            concept: key,
            percentage_present: conceptTypicality[key]['percent_present'],
            percentage_correct: conceptTypicality[key]['percent_correct'] * conceptTypicality[key]['percent_present'],
            typicality: conceptTypicality[key]['typicality']
        });
    }

    let columns = [];
    let height = 0;
    for (let key in matrixImages) {
        if (height < matrixImages[key]["images"].length) {
            height = matrixImages[key]["images"].length
        }   
    }
    for (let key in matrixImages) {
        const [gt, label] = key.replace("_classified_as_"," ").split(" ");
        let images = [];
        for(let image in matrixImages[key]["images"]) {
            
            images.push({
                view:
                    <>
                    {/* Image in column */}
                    <div className="hover-click-pair" onClick={() => fillModalData(matrixImages[key]["heatmaps"][image],matrixImages[key]["images"][image], matrixImages[key]["annotations"],gt,label, matrixImages[key]["confidence"] ) }>
                        <img className="matrixImage" src={'data:image/jpeg;base64,' + matrixImages[key]["heatmaps"][image]}
                            style={{"width": 100 + "px", height: 100 + "px"}}></img>
                        <img className="matrixImage" src={'data:image/jpeg;base64,' + matrixImages[key]["images"][image]}
                            style={{"width": 100 + "px", height: 100 + "px"}}></img>
                    </div>
                  </>
            })
        }

        columns.push({
            view:
                <div className="imageColumn d-flex flex-column" style={{"height": (height * 500 * matrixImages.length).toString() + "px" }}>
                    <h3 className={"imageColumnTitle"}>{key.replace(/_/g, " ")}</h3>
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

    // field based on which the array is ordered
    function sort(array, on) {
        for (let i = 0; i < array.length; i++) {
            var min_idx = i;
            for (let j = i + 1; j < array.length; j++) {
                if (array[j][on] < array[min_idx][on]) {
                    min_idx = j;
                }
            }
            [array[min_idx], array[i]] = [array[i], array[min_idx]]
        }
        return array
    }

    const size = 475;
    const concept_data_view = [];
    sort(concept_data, sorting);
    for (let i = 0; i < concept_data.length; i++) {
        concept_data_view.push({
        view:
            <div className={"conceptRow" + (i%2).toString()}>
                <Collapse>
                    <Panel header={concept_data[i].concept}>
                        <h5>
                            {concept_data[i].concept}
                        </h5>
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
                    </Panel>
                </Collapse>
            </div>
        })
    }

    // Add the data into the matrix only once the page is loaded.
    useEffect(() => {
        getMatrixData();
        getMatrixImages(1, 2);
        getScores(1, 2); // Attempt to already have 1 cell selected
        getF1()
    }, [0]);


    // Used for the lower value in each cell.
    function sumColumn (col) {
        let column_sum = 0
        for (let i = 0; i < absoluteData.length; i++) {
            column_sum += absoluteData[i][col]
        }
        return column_sum
    }

    // Intended for Prediction<->Truth
    function switchLabel(array) {
        let aux = array[0]
        array[0] = array[1]
        array[1] = aux
        return array
    }

    function transpose (arr)  {
       for (let i = 0; i < arr.length; i++) {
          for (let j = 0; j < i; j++) {
             const tmp = arr[i][j];
             arr[i][j] = arr[j][i];
             arr[j][i] = tmp;
          };
       }
    }

    let labels1 = ["Prediction", "Ground Truth"]
    let [labelState, setLabelState] = useState(true);
    let [labels, setLabels] = useState(labels1);

    return (
        <div id={"entire-page"}>
            <div class={"errorDiv"}>
            </div>
            <Row>
                <Col span={12}>
                    <div className="quadrant">
                        <div>
                            <h2 className={"quadrantTitle"}>Confusion Matrix</h2>
                            <button id={"switchDashboard"} onClick={() => {
                                setLabelState(!labelState);
                                setLabels(switchLabel(labels));
                                transpose(relativeData);
                                transpose(absoluteData);
                            }}>Switch between Prediction and Truth values</button>

                            <p id={"horizontal-label"}>{labels[0]}</p>
                            <div className={"table-label"}>
                                <p id={"vertical-label"}>{labels[1]}</p>
                                {/*td = the blank cell in the top left corner*/}
                                <table className='Matrix-header'>
                                    {/*F1 score above matrix*/}
                                    {
                                        <tr>
                                            <th className={"f1score"}><em>F1 Score</em></th>
                                            {f1_scores.map(item => (
                                                <th className={"f1score"} scope="col" key={item}><em>{item}</em></th>
                                            ))}
                                        </tr>
                                    }

                                    {/*Matrix data comes below*/}
                                    <tr>
                                        <td className={'Empty-cell'} id={"elem0"}/>
                                        {categories.map(item => (
                                            <th className={"category"} scope="col" key={item.id}>{item}</th>
                                        ))}
                                    </tr>
                                    {relativeData.map((x, key1) => (
                                        <tr>
                                            <th scope="row" className={"category"}>{categories[key1]}</th>
                                            {x.map((item, key2) => (key1 !== key2) ? (
                                                <td className={"off-diagonal"} id={"elem" + item}>
                                                    <div>
                                                        <button type={"button"} className={"button"} id={"elem" + item}
                                                            onClick={() => {
                                                                getMatrixImages(key1, key2);
                                                                getScores(key1, key2);
                                                                getBinaryData(key1, key2);
                                                            }}>{item}%
                                                        </button>
                                                    </div>
                                                    <div>
                                                        <button type={"button"} className={"button"} id={"elem" + item}
                                                            style={{"fontSize": "10px"}} onClick={() => {
                                                                getMatrixImages(key1, key2);
                                                                getScores(key1, key2);
                                                                getBinaryData(key1, key2);
                                                            }}>{absoluteData[key1][key2] + " / " + totalImages}
                                                        </button>
                                                    </div>
                                                </td>
                                                ) : (
                                                    <td className={"diagonal-cell"} id={"elem" + item}>
                                                        <div>
                                                            <button type={"button"} className={"button"} id={"elem" + item}
                                                                onClick={() => {
                                                                    getMatrixImages(key1, key2);
                                                                    getScores(key1, key2);
                                                                    getBinaryData(key1, key2);
                                                                }}>{item}%
                                                            </button>
                                                        </div>
                                                        <div>
                                                            <button type={"button"} className={"button"} id={"elem" + item}
                                                            style={{"fontSize": "10px"}} onClick={() => {
                                                                    getMatrixImages(key1, key2);
                                                                    getScores(key1, key2);
                                                                    getBinaryData(key1, key2);
                                                                }}>{absoluteData[key1][key2] + " / " + totalImages}
                                                            </button>
                                                        </div>
                                                    </td>
                                                )
                                            )}
                                        </tr>
                                    ))}
                                </table>
                            </div>
                        </div>
                    </div>
                </Col>


                <Col span={12}>
                    <div className="quadrant" id={"quadrant1"}>
                        <h2 className={"quadrantTitle"}>Matrix Concepts</h2>
                        <div className="charts-concepts">
                            <div className={"charts"}>
                                <Pie
                                    data = {{
                                        labels: chartData.labels,
                                        datasets: chartData.datasets
                                    }}
                                    options = {{
                                        radius: "100%",
                                        maintainAspectRatio: true,
                                    }}
                                />
                                <br></br>
                                <div className="subtitle"><h3>Ordering</h3></div>
                                <RadioGroup value={sorting} onChange={(event) => {
                                    setSorting(event.target.value);
                                    sort(concept_data, sorting);
                                }}>
                                    <Radio value={"concept"}>Alphabetical order</Radio><br/>
                                    <Radio value={"typicality"}>Typicality</Radio><br/>
                                    <Radio value={"percentage_correct"}>Percentage of correct classification</Radio><br/>
                                    <Radio value={"percentage_wrong"}>Percentage of wrong classification</Radio><br/>
                                </RadioGroup>
                            </div>
                            {
                                columns.map(item => (
                                    <>
                                        {item.view}
                                    </>
                                ))
                            }
                        </div>
                        <br/>
                            {
                                <div>
                                    {
                                        concept_data_view.map(item => (
                                            <>
                                                {item.view}
                                            </>
                                        ))
                                    }
                                </div>
                            }
                    </div>
                </Col>
            </Row>

            <Row>
                <Col span={24}>
                    <div className="py-2 pr-3">
                        <div className="quadrant w-100">
                            <QueryClassificationFormulas />
                        </div>
                    </div>
                </Col>
            </Row>
            <Modal show={showModal} onHide={() => {setShowModal(false)}}      >
                        <Modal.Header closeButton closeLabel="close window">
                        <h4>Details for {modalData["gt"]}</h4>
                        </Modal.Header>
                        <Modal.Body>
                            <div className="d-flex">
                                <div className="row">
                                    <div className="col-12">
                                        <p>Classified as: {modalData["label"]} (Confidence: {modalData["confidence"] === null ? "unknown" :modalData["confidence"] +'%'})</p>
                                    </div>
                                    <div className="col-12">
                                        <img src={'data:image/jpeg;base64,' + modalData["image"]}></img>
                                        <p>original image</p>
                                    </div>
                                    <div className="col-12">
                                        <img src={'data:image/jpeg;base64,' + modalData["heatmap"]}></img>
                                        <p>heatmap</p>
                                    </div>
                                </div>
                            </div>
                            {modalData["annotations"]  ?
                            <>
                            <h5>Annotated concepts ({modalData["annotations"].length}):</h5>
                            <ul>
                                {modalData["annotations"].map(a => <li>{a}</li>)}
                            </ul>
                            </>
                            :
                            <h3>No annotated concepts have been found</h3>
                            }
                        </Modal.Body>
            </Modal>
        </div>
    );
}
