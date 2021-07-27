import axios from "axios";
import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "../../css/ConfusionMatrix.less";
import {Row, Col, Collapse, Radio} from "antd";
import 'bootstrap/dist/css/bootstrap.min.css';
import {f1 as f1_url, accuracy as accuracy_url, matrix_data as matrix_data_url} from "../../API";

export default function ConfusionMatrix(props) {

    let [relativeData, setRelativeData] = useState([]);
    let [absoluteData, setAbsoluteData] = useState([0, 0]);
    let [totalImages, setTotalImages] = useState(0);
    let [categories, setCategories] = useState([]);
    let [available_sessions, set_available_sessions] = useState([])

    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );
    const session_id = useState(JSON.parse(sessionStorage.getItem("session")))
    let [f1_scores, setF1_scores] = useState([]);
    let [accuracy_scores, setAccuracy_scores] = useState([]);
    const getMatrixData = (event) => {

        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        axios
            .get(
                matrix_data_url,
                {
                    headers: {
                        "Content-Type": "application/json" ,
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
                e.innerHTML = "Something went wrong when retrieving the confusion matrix. Try again later."
                e.className = "error"
                errorDiv.appendChild(e)

                setRelativeData([]);
                setAbsoluteData([]);
                setCategories([]);
            });
    };

    const getF1 = () => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];

        axios
            .post(
                f1_url,
                {
                    "session_id": session_id[0]
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "Token " + token,
                    }
                })
            .then(response => {
                    setF1_scores(response.data)
                }
            )
            .catch(function (error) {
                const e = document.createElement("div")
                e.innerHTML = "Something went wrong when retrieving the f1 scores. Try again later."
                e.className = "error"
                errorDiv.appendChild(e)

                setF1_scores([]);
            });
    }

    const getAccuracy = () => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];

        axios
            .post(
                accuracy_url,
                {
                    "session_id": session_id[0]
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "Token " + token,
                    }
                })
            .then(response => {
                    setAccuracy_scores(response.data)
                }
            )
            .catch(function (error) {
                const e = document.createElement("div")
                e.innerHTML = "Something went wrong when retrieving the accuracy scores. Try again later."
                e.className = "error"
                errorDiv.appendChild(e)

                setAccuracy_scores([]);
            });
    }

    let labels1 = ["Prediction", "Ground Truth"]
    let [labelState, setLabelState] = useState(true);
    let [labels, setLabels] = useState(labels1);

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

    // Add the data into the matrix only once the page is loaded because of [0].
    useEffect(() => {
        const errorDiv = document.getElementsByClassName("errorDiv")[0];
        errorDiv.innerHTML = ""
        getMatrixData()
        getF1()
        getAccuracy()
    }, [0]);

    return (
        <div>
            <div className="errorDiv"></div>
            <h2>Confusion Matrix</h2>
            <p>Select the cells of the confusion matrix to get more information on the rules and concepts behind
                the correlation of the ground truth and the prediction. In each cell, the upper percentage value is relative either to the ground truth or the absolute prediction.</p>
            <p> Overall accuracy: {accuracy_scores} </p>
            <button id={"switch"} onClick={() => {
                setLabelState(!labelState);
                setLabels(switchLabel(labels));
                transpose(relativeData);
                transpose(absoluteData);
            }}>Switch between Prediction and Truth values</button>
            <p id={"horizontal-label"}>{labels[0]}</p>
            <div className={"table-label"}>
                <p id={"vertical-label"}>{labels[1]}</p>
                {/*td = the blank cell in the top left corner*/}
                
                <table className='Matrix-table'>
                    {/*F1 score above matrix*/}
                    {
                        <tr>
                            <td className={"f1score"} style={{"fontSize": "10x"}}><em>F1 Score</em></td>
                            {f1_scores.map(item => (
                                <td className={"f1score"}  scope="col" key={item} style={{"fontSize": "10x"}}><em>{item}</em></td>
                            ))}
                        </tr>
                    }

                    <tr>
                        <td className={'Empty-cell'} id={"elem0"}/>
                        {categories.map(item => (
                            <th className={'Header-cell'} scope="col" key={item.id}>{item}</th>
                        ))}
                    </tr>
                    {relativeData.map((x, key1) => (
                        <tr>
                            <th scope="row">{categories[key1]}</th>
                            {x.map((item, key2) => (key1 !== key2) ? (
                                <td className={"off-diagonal"} id={"elem" + item}>
                                    <div>
                                        <Link className={"link"} to={{
                                            pathname: "/classification/" + categories[key1] + "/" + categories[key2],
                                            state:
                                                [
                                                    categories,
                                                    [categories[key1], categories[key2]],
                                                    [absoluteData[key1][key2], absoluteData[key2][key1], absoluteData[key1][key1], absoluteData[key2][key2]]
                                                ]
                                        }} key={key1 + key2}>{item}%</Link>
                                    </div>
                                    <div>
                                        <Link className={"link"} style={{"fontSize": "10px"}} to={{
                                            pathname: "/classification/" + categories[key1] + "/" + categories[key2],
                                            state:
                                                [
                                                     categories,
                                                    [categories[key1], categories[key2]],
                                                    [absoluteData[key1][key2], absoluteData[key2][key1], absoluteData[key1][key1], absoluteData[key2][key2]]
                                                ]
                                        }} key={key1 + key2}>{absoluteData[key1][key2] + " / " + totalImages}</Link>
                                    </div>
                                </td>
                                ) : (
                                    <td bgcolor={"green"} className={"diagonal-cell"} id={"elem" + item}>
                                        <div>
                                            <Link className={"link"} to={{
                                                pathname: "/correct-classification/" + categories[key1] + "/" + categories[key2],
                                                state:
                                                    [
                                                        categories,
                                                        [categories[key2], categories[key2 + 1],
                                                            categories[key1],
                                                            key1 < absoluteData.length -1 ? categories[key1 + 1]: categories[key1 - 1]],
                                                        absoluteData[key1],
                                                        [
                                                            absoluteData[key1][key2], absoluteData[key1][key2 + 1],
                                                            key1 < absoluteData.length - 1 ? absoluteData[key1 + 1][key2] :  absoluteData[key1 - 1][key2],
                                                            key1 < absoluteData.length - 1 ? absoluteData[key1 + 1][key2 + 1] : absoluteData[key1 - 1][key2 + 1]                                                        ],
                                                        [categories[key1], categories[key2]]
                                                    ]
                                            }} key={key1 + key2}>{item}%</Link>
                                        </div>
                                        <div>
                                            <Link className={"link"} style={{"fontSize": "10px"}} to={{
                                                pathname: "/correct-classification/" + categories[key1] + "/" + categories[key2],
                                                state:
                                                    [
                                                        categories,
                                                        [categories[key2], categories[key2 + 1],
                                                            categories[key1],
                                                            key1 < absoluteData.length -1 ? categories[key1 + 1] : categories[key1 - 1]],
                                                        absoluteData[key1],
                                                        [
                                                            absoluteData[key1][key2], absoluteData[key1][key2 + 1],
                                                            key1 < absoluteData.length - 1 ? absoluteData[key1 + 1][key2] :  absoluteData[key1 - 1][key2],
                                                            key1 < absoluteData.length - 1 ? absoluteData[key1 + 1][key2 + 1] : absoluteData[key1 - 1][key2 + 1]                                                      ],
                                                        [categories[key1], categories[key2]]
                                                    ]
                                            }} key={key1 + key2}>{absoluteData[key1][key2] + " / " + totalImages}</Link>
                                        </div>
                                    </td>
                                )
                            )}
                        </tr>
                    ))}
                </table>
                
            </div>
        </div>
    );
}