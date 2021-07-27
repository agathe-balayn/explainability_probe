import React, {useEffect, useState} from 'react';
import { Link } from "react-router-dom";
import { Button } from "antd";
import axios from "axios";
import Modal from 'react-bootstrap/Modal'
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
    const session_id = useState(JSON.parse(sessionStorage.getItem("session")))
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState([]);

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
        //getScores();
        getMatrixImages();
    }, [0] );

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

    const columns = []
    let height = 0;
    for (let key in matrixImages) {
        if (height < matrixImages[key]["images"].length) {
            height = matrixImages[key]["images"].length
        }
    }
    for (let key in matrixImages) {
        const images = []
        const [gt, label] = key.replace("_classified_as_"," ").split(" ");
        for(let image in matrixImages[key]["images"]) {
            images.push({
                view:
                <div className="hover-click-pair d-inline-flex m-4" onClick={() => 
                    fillModalData(
                        matrixImages[key]["heatmaps"][image],
                        matrixImages[key]["images"][image],
                        matrixImages[key]["annotations"][image],
                        gt,
                        label, 
                        matrixImages[key]["confidence"][image] 
                        ) }>
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
