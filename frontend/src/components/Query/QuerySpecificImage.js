import React from 'react';
import {  Input, Radio, Select, Button, Checkbox } from 'antd';
import "../../css/QuerySpecificImage.less"
import axios from "axios";
import {query_specific_url} from "../../API";
const { Option } = Select;

class QuerySpecificImage extends React.Component {
    state = {
        numConcepts: 0,
        imageSet: 1,
        images: [],
        session_id : JSON.parse(sessionStorage.getItem("session")),
        session_image_count: 0,
        correct_images: 0
    }

    changeImageSet = (e) => {
        this.setState({
            imageSet: e.target.value
        });
    }

    deselectedSelection = () => {
        this.setState({
            numClasses: 0
        })
    }

    selectedSelection = () => {
        this.setState({
            numClasses: 1
        })
    }

    addClassInput = () => {
        this.setState({
            numClasses: this.state.numClasses + 1
        })
    }
    removeClassInput = () => {
        if(this.state.numClasses > 1) {
            this.setState({
                numClasses: this.state.numClasses - 1
            })
        }
    }

    onAddChild = () => {
        this.setState({
            numConcepts: this.state.numConcepts + 1
        });
    }

    onRemoveChild = () => {
        if(this.state.numConcepts > 0) {
            this.setState({
                numConcepts: this.state.numConcepts - 1
            });
        }
    }

    /**
     * get data from backend and display it
     * @param event
     */
    getImages = (event) => {
        const errors = document.getElementsByClassName("errorDiv")[1]
        errors.innerHTML = ""
        document.getElementById("placeholder").innerText = "loading..."
        let orQuery = []
        let andPart = document.getElementById("conceptImages0").value
        let orExclude = []
        let orNotQuery = []
        for (let i = 1; i < this.state.numConcepts + 1; i++) {
            let not = document.getElementById("checkbox" + i).checked
            let select = document.getElementById("select" + i).value
            if(not) {
                if(select === "AND") {
                    orExclude.push(document.getElementById("conceptImages" + i).value)
                }else if (select === "OR"){
                    orNotQuery.push(document.getElementById("conceptImages" + i).value)
                }
            } else {
                if (select === "OR") {
                    orQuery.push(andPart)
                    andPart = ""
                } else {
                    andPart += " AND "
                }
                andPart += document.getElementById("conceptImages" + i).value
            }
        }

        if(andPart.length > 0) {
            orQuery.push(andPart)
        }
        let settings = [null, "all", "correct_only", "incorrect_only"]
        let data = {};
        data['image_setting'] = settings[this.state.imageSet]
        data['session_id'] = this.state.session_id
        if(orQuery.length > 0) {
            data['or_query'] = orQuery
        }
        if(orNotQuery.length > 0){
            data["or_not_query"] = orNotQuery
        }
        if(orExclude.length > 0){
            data["or_exclude"] = orExclude
        }
        let categorization = document.getElementById("isClass").value
        if(categorization !== "") {
            data['only_true_class'] = [categorization]
        }

        let predicted_class = document.getElementById("predictedClass").value
        let checked = document.getElementById("checkbox").checked
        if(predicted_class !== "") {
            if(checked){
                data['exclude_predicted_class'] = [predicted_class]
            }else{
                data['only_predicted_class'] = [predicted_class]
            }

        }
        this.setState({
            images: []
        })
        document.getElementById("loadingInfo").innerHTML = "loading..."
        axios
            .post(
                query_specific_url,
                data,
                {
                    headers: {
                        "Content-Type": "application/json" ,
                        Authorization: "Token " + JSON.parse(sessionStorage.getItem("token"))
                    }
                }
            )
            .then(r => {
                document.getElementById("loadingInfo").innerHTML = ""
                if(r['data']['image_data'].length == 0){
                    this.setState({
                        images: -1,
                        session_image_count: 0
                    })
                }else{
                    this.setState({
                        images:r['data']['image_data'],
                        session_image_count:r['data']['image_count'],
                        correct_images: r['data']['correctly_classified_images']
                    })
                }

            }).catch(function (exception) {
                            document.getElementById("loadingInfo").innerHTML = ""
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the request. Try again later."
                            errors.appendChild(error)
                    })
    }

    render() {

        let images_view = []
        let statistical_info = []
        if(this.state.images == -1){
            document.getElementById("loadingInfo").innerHTML = "There were no images available"
        }else{
            if(this.state.images.length > 0){
                statistical_info.push(
                    <tr>
                        <th>Statistical information on the queried images</th>
                        <th>values</th>
                    </tr>
                )
                images_view.push(
                    <tr>
                        <th>true class</th>
                        <th>predicted class</th>
                        <th>present concepts</th>
                        <th>image</th>
                        <th>saliency map</th>
                    </tr>)
            }
            
            for(let i = 0; i < this.state.images.length; i++){
                if(this.state.images[i]['classification_check'] == 'Correctly classified'){
                    images_view.push(
                        <tr>
                            <td>{this.state.images[i]['true_class']}</td>
                            <td>{this.state.images[i]['predicted_class']}</td>
                            <td>{this.state.images[i]['rules'].substring(0, this.state.images[i]['rules'].length-2)}</td>
                            <td>
                                <img src={'data:image/jpeg;base64,' + this.state.images[i]['image']} alt={"image of" + this.state.images[i]['true_class']} class={'trueImage'}/>
                            </td>
                            <td>
                                <img src={'data:image/jpeg;base64,' + this.state.images[i]['saliency_map']} alt={"image of" + this.state.images[i]['true_class']} class={'trueImage'}/>
                            </td>
                        </tr>
                    )
                }

                else{
                    images_view.push(
                        <tr>
                            <td>{this.state.images[i]['true_class']}</td>
                            <td>{this.state.images[i]['predicted_class']}</td>
                            <td>{this.state.images[i]['rules'].substring(0, this.state.images[i]['rules'].length-2)}</td>
                            <td>
                                <img src={'data:image/jpeg;base64,' + this.state.images[i]['image']} alt={"image of" + this.state.images[i]['true_class']} class={'incorrectImage'}/>
                            </td>
                            <td>
                                <img src={'data:image/jpeg;base64,' + this.state.images[i]['saliency_map']} alt={"image of" + this.state.images[i]['true_class']} class={'incorrectImage'}/>
                            </td>
                        </tr>
                    )
                }

            }

            if(this.state.session_image_count > 0) {
                statistical_info.push(
                    <tr>
                        <td>Images found</td>
                        <td>{this.state.images.length}</td>
                    </tr>
                )

                statistical_info.push(
                    <tr>
                        <td>Total images in dataset</td>
                        <td>{this.state.session_image_count}</td>
                    </tr>
                )

                statistical_info.push(
                    <tr>
                        <td>Fraction of correctly attributed images</td>
                        <td>{this.state.correct_images} / {this.state.images.length}</td>
                    </tr>
                )

            }
        }


        function checkboxChange(e) {
            if (!e.target.checked) {
                let del = document.createElement('del')
                del.innerHTML = "not"
                document.getElementById("notLbl").innerHTML = ""
                document.getElementById("notLbl").appendChild(del)
            } else {
                document.getElementById("notLbl").innerHTML = "not"
            }
        }

        let conceptList = []

        let numConcepts = this.state.numConcepts
        for(let i = 0; i < this.state.numConcepts; i++) {
            conceptList.push(
                <span className={"extraConcept"}>
                    <Checkbox className={"checkbox"} id={"checkbox" + (i+1)}>
                        not
                    </Checkbox>
                        <div>
                            <select className={"select"} id={"select" + (i + 1)}
                                    style={{width: 80, textAlign: 'center', height: 35}}>
                                <option value="AND">AND</option>
                                <option value="OR">OR</option>
                            </select>
                        </div>
                    <Input id={"conceptImages" + (i + 1)} className="concept" placeholder={"Concept " + (i+2)}
                           style={{width: 200, textAlign: 'center', height: 30}}/>
                </span>
            )
        }

        return (
            <div id="QuerySpecificImage">
                <div className="errorDiv">
                </div>
                <h1>Query specific images</h1>
                <p>Query images based on their actual class and predicted class</p>
                <div id={"QueryParams"}>
                    <div id={"selectGroup"}>
                        <label id={"label1"}>Query Concept</label>
                        <Input style={{width: 200, textAlign: 'center', height: 30}} placeholder="Concept 1" id={"conceptImages0"}/>
                        <Button onClick={this.onAddChild} id={"addConceptButton"}>+ add concept</Button>
                        <Button onClick={this.onRemoveChild} id={"removeConceptButton"}>- remove concept</Button>
                        <div id={"extraConcepts"}>
                            {conceptList}
                        </div>
                    </div>
                    <div id={"inputImages"}>
                        <Input id={"isClass"} className="concept" placeholder="actual class..."
                               style={{width: 200, textAlign: 'center', height: 35}}/>
                        <div id={"selector"}>
                            <p className={"select"}>
                                and
                            </p>
                        </div>
                        <Checkbox className={"checkbox"} id={"checkbox"} onChange={checkboxChange}>
                            <label id={"notLbl"}>
                                <del>not</del>
                            </label>
                        </Checkbox>
                        <Input id={"predictedClass"} className="concept" placeholder="predicted class..."
                               style={{width: 200, textAlign: 'center', height: 35}}/>
                    </div>
                </div>
                <div id={"Settings"}>
                    <h2 id={"settingTitle"}>settings:</h2>
                    <span id={"radios"}>
                        <div id={"imagesSettings"}>
                            <h3 className={"querySettingTitle"}>Set of images considered for the computations</h3>
                            <Radio.Group id={"imagesSettingsGroup"} onChange={this.changeImageSet} defaultValue={1}>
                                <Radio value={1}>All images</Radio>
                                <Radio value={2}>Only images with correct classification</Radio>
                                <Radio value={3}>Only images with incorrect classification</Radio>
                            </Radio.Group>
                        </div>
                    </span>
                </div>
                <Button onClick={this.getImages}>show images</Button>
                <p id={"loadingInfo"}/>
                <table>
                    {statistical_info}
                </table>
                <p>  </p>
                <table>
                    {images_view}
                </table>
            </div>
        );
    }
}

export default QuerySpecificImage;
