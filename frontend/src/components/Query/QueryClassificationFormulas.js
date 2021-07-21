import React from 'react';
import axios from "axios";
import {Input, Radio, Select, Button, Checkbox, InputNumber, Slider} from 'antd';
import {query_rules_url, query_concept_matrix_url, query_scores_url} from "../../API";

const { Option } = Select;

class QueryClassificationFormulas extends React.Component {
    state = {
        numClasses : 0,
        numConcepts: 0,
        confusion_matrix: 0,
        imageSet: 1,
        classes : [],
        rel_matrix: [],
        concept_typicality: [],
        rule_typicality: [],
        typicalities: 0,
        antecedent : 3,
        session_id: JSON.parse(sessionStorage.getItem("session")),
    }

    /**
     * sorts list of rules by inputted value
     * @param e event containing the selected sorter
     */

    sortRulesByFilter = (e) =>{
        this.setState({
            rule_typicality: this.sortRulesBy(this.state.rule_typicality, e)
        })
    }

    /**
     * sorts list of concepts by inputted value
     * @param e event containing the selected sorter
     */

    sortConceptsByFilter = (e) =>{
        this.setState({
            concept_typicality: this.sortConceptsBy(this.state.concept_typicality, e),
        })
    }

    /**
     * sorts list of rules by inputted value
     * @param data array of rules
     * @param by parameter to sort by
     * @returns {{}} returns sorted array
     */

    sortRulesBy = (data, by) =>{
        let items = Object.keys(data).map(function(key) {
            return [key, data[key]];
        });
        items.sort(function(first, second) {
            let first2 = 0
            for(let i in first[1]){
                if(first2 === 0){
                    first2 = first[1][i][by]
                }

                //first2=first[i][by]
            }
            let second2 = 0
            for(let i in second[1]){
                if(second2===0){
                    second2=second[1][i][by]
                }
            }
            return first2 - second2;
        });
        let newData = {}
        for(let i = 0; i < items.length; i++){
            newData[items[i][0]] = items[i][1]
        }
        return newData;
    }

    /**
     * sorts list of concepts by inputted value
     * @param data array of rules
     * @param by parameter to sort by
     * @returns {{}} returns sorted array
     */

    sortConceptsBy = (data, by) => {
        let items = Object.keys(data).map(function(key) {
            return [key, data[key]];
        });
        items.sort(function(first, second) {
            return first[1][by] - second[1][by];
        });
        let newData = {}
        for(let i = 0; i < items.length; i++){
            newData[items[i][0]] = items[i][1]
        }
        return newData;
    }

    /**
     * get typicality stores from backend
     * @param e event
     */
    getTypicalityScore = (e) => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        errors.innerHTML = ""
        let data = this.getAllData()

        axios
            .post(
                query_scores_url,
                data,
                {
                    headers: {
                        "Content-Type": "application/json" ,
                        Authorization: "Token " + JSON.parse(sessionStorage.getItem("token"))
                    }
                }
            )
            .then(r => {
                document.getElementById("placeholder").innerText = ""
                this.setState({
                    typicalities: 1,
                    concept_typicality: r.data['concepts'],
                    rule_typicality: r.data['rules']
                })
                let sum = 0
                for(let i in r.data['rules']){
                    sum ++;
                }
                if(sum === 0){
                    this.setState({
                        typicalities: -1
                    })
                }

            }).catch(function (exception) {
                            document.getElementById("placeholder").innerHTML = ""
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the request. Try again later."
                            errors.appendChild(error)
                    })

    }

    /**
     * gather data from all input fields
     * @returns {{}} returns input data for query
     */

    getAllData = () => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        errors.innerHTML = ""
        document.getElementById("placeholder").innerText = "loading..."
        let orQuery = []
        let andPart = document.getElementById("concept0").value
        let orExclude = []
        let orNotQuery = []
        let categorization = []
        for (let i = 1; i < this.state.numConcepts + 1; i++) {
            let not = document.getElementById("checkbox" + i).checked
            let select = document.getElementById("select" + i).value
            /*
            if(not) {
                if(select === "AND") {
                    orExclude.push(document.getElementById("concept" + i).value)
                }else if (select === "OR"){
                    orNotQuery.push(document.getElementById("concept" + i).value)
                }
            } else {
                if (select === "OR") {
                    orQuery.push(andPart)
                    andPart = ""
                } else {
                    andPart += " AND "
                }
                andPart += document.getElementById("concept" + i).value
            }
            */
            if (select === "OR") {
                
                orQuery.push(andPart)
                andPart = ""
                if (not) {
                    andPart += "NOT "
                } 
                
            } else {
                andPart += " AND "
                if (not){
                    andPart += "NOT "
                }
            }
            andPart += document.getElementById("concept" + i).value

        }

        if(andPart.length > 0) {
            orQuery.push(andPart)
        }
        let settings = [null, "all", "correct_only", "incorrect_only"]
        let data = {};
        data['image_setting'] = settings[this.state.imageSet]
        if(orQuery.length > 0) {
            data['or_query'] = orQuery
        }
        data["max_antecedent_length"] = this.state.antecedent;
        if(orNotQuery.length > 0){
            data["or_not_query"] = orNotQuery
        }
        if(orExclude.length > 0){
            data["or_exclude"] = orExclude
        }
        //categorization.push(document.getElementById("lsInput").value)
        //console.log("test categorization")
        //console.log(categorization)
        //if(categorization !== "") {
        //    console.log("gkjhgkjh")
        //    data['only_true_class'] = [""] //categorization
        //}
        let selectedClasses = []
        for(let i = 0; i < this.state.numClasses; i++){
            selectedClasses.push(document.getElementById("classesInput" + i).value)
        }
        if(selectedClasses.length > 0){
            data['class_selection'] = selectedClasses
        }
        this.setState({
            typicalities: 0,
            confusion_matrix: 0
        })
        data['session_id'] = this.state.session_id
        return data;
    }

    /**
     * process data into confusion matrix form
     * @param r response from backend
     */

    processConfusionMatrixData (r) {
        document.getElementById("placeholder").innerText = "";
        let matrix_top = []
        let matrix_bottom = []
        let classes = []

        // prepare list of classes.
        for(let i in r.data.top_number){
            //console.log(i)
            if (!classes.includes(i)){
                classes.push(i)
            }
        }
        //console.log(classes)
        // prepare matrix
        let idx_row = 0
        for(let i in classes){
            //console.log("i")
            //console.log(classes[i])
            matrix_top[idx_row] = []
            matrix_bottom[idx_row] = []
            //console.log(matrix_top)
            let idx_col = 0
            for (let j in classes){
                matrix_top[idx_row][idx_col] = []
                matrix_top[idx_row][idx_col][0] = r.data.top_number[classes[i]][classes[j]]
                matrix_top[idx_row][idx_col][1] = r.data.bottom_number[classes[i]][classes[j]]
                matrix_bottom[idx_row][idx_col] = r.data.bottom_number[classes[i]][classes[j]]
                idx_col ++
            }
            idx_row ++
        }
        


        /*
        let rules = r.data.rules
        //let classes = []
        let matrix = []
        //[actual, predicted]
        let images = []
        let correctFormat = []
        let index = 0;

        for(let i in rules){
            for(let j in rules[i]){
                for(let z in rules[i][j]){
                    if(z.includes(".jpg")){
                        if(!images.includes(z)){
                            images.push(z)
                            correctFormat[index] = []
                            correctFormat[index][0] = rules[i][j][z]
                            correctFormat[index][1] = j
                            index++;
                        }
                        if(!classes.includes(rules[i][j][z])) {
                            classes.push(rules[i][j][z])
                        }
                    }
                }
                if(!classes.includes(j)) {
                    classes.push(j)
                }
            }
            //index++;
        }
        for(let i = 0; i < classes.length; i++){
            matrix[i] = []
            for(let j = 0; j < classes.length; j++){
                matrix[i][j] = 0;
            }
        }

        for(let i = 0; i < correctFormat.length; i++){
            let indexA = classes.indexOf(correctFormat[i][0])
            let indexB = classes.indexOf(correctFormat[i][1])
            if(indexA >= 0 && indexB >= 0){
                matrix[indexA][indexB] += 1
            }

        }
        let rel_matrix = []
        for(let row = 0; row < matrix.length; row ++){
            rel_matrix[row] = []
            let count = 0
            for(let i = 0; i < matrix[row].length; i++){
                count += matrix[row][i]
            }
            if(count === 0) {
                count = 1;
            }
            for(let j = 0; j<matrix[row].length; j++){
                rel_matrix[row][j] = (Math.round(matrix[row][j]*10000.0/count)/100.0)
            }
        }
        */
        if(classes.length === 0){
            this.setState({
                confusion_matrix: -1
            })
        }else{
            this.setState({
                confusion_matrix: 1
            })
        }
        this.setState({
            classes : classes,
            rel_matrix: matrix_top//rel_matrix
        })
    }

    /**
     * get data for confusion matrix
     * @param e event
     */

    getConfusionMatrix = (e) => {
        const errors = document.getElementsByClassName("errorDiv")[0]
        errors.innerHTML = ""
        let data = this.getAllData()
        axios
            .post(
                query_concept_matrix_url,
                data,
                {
                    headers: {
                        "Content-Type": "application/json" ,
                        Authorization: "Token " + JSON.parse(sessionStorage.getItem("token"))
                    }
                },
            )
            .then(r => {
                this.processConfusionMatrixData(r)
            }).catch(function (exception) {
                            document.getElementById("placeholder").innerHTML = ""
                            const error = document.createElement("div")
                            error.className = "error"
                            error.innerHTML = "Something went wrong with processing the request. Try again later."
                            errors.appendChild(error)
                    })

    }

    onAddChild = () => {
        this.setState({
            numConcepts: this.state.numConcepts + 1
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

    changeImageSet = (e) => {
        this.setState({
            imageSet: e.target.value
        });
    }

    onRemoveChild = () => {
        if(this.state.numConcepts > 0) {
            this.setState({
                numConcepts: this.state.numConcepts - 1
            });
        }
    }

    render() {
        let conceptList = []
        let confusionMatrix = []

        /**
         * add confusion matrix cells
         */
        for(let i = 0 ; i < this.state.confusion_matrix; i++){
            confusionMatrix = []
            confusionMatrix.push(<div>
                <table className='Matrix-header'>
                    <tr>
                        <td className={'Empty-cell'}/>
                        {this.state.classes.map(item => (
                            <th className={'Header-cell'} scope="col" key={item.id}>{item}</th>))}
                    </tr>
                    {this.state.rel_matrix.map((x, key1) => (

                        <tr>
                            <th scope="row">{this.state.classes[key1]}</th>
                            {x.map((item, key2) => key1 !== key2 ? (
                                    <td>
                                        <div>
                                            {item[0]}%
                                        </div>
                                        <div>
                                            {item[1]}%
                                        </div>
                                    </td>
                                ) : (
                                    <td>
                                        <div>
                                            {item[0]}%
                                        </div>
                                        <div>
                                            {item[1]}%
                                        </div>
                                    </td>
                                )
                            )}
                        </tr>
                    ))}
                </table>
            </div>)
        }

        /**
         * display concept input fields
         */
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
                    <Input id={"concept" + (i + 1)} className="concept" placeholder={"Concept " + (i+2)}
                           style={{width: 200, textAlign: 'center', height: 30}}/>
                </span>
            )
        }

        /**
         * convert concept typicality into readable format
         */
        let concept_data = [];
        for (let key in this.state.concept_typicality) {
            
            concept_data.push({
                concept: this.state.concept_typicality[key]['concept_name'],
                percentage_present: this.state.concept_typicality[key]['percent_present'],
                percentage_correct: this.state.concept_typicality[key]['percent_correct'], 
                typicality: this.state.concept_typicality[key]['typicality']
            });
        }

        const rule_data = [];
        const concept_data_view = [];

        /**
         * convert rule typicality into readable format
         */
        for (let key in this.state.rule_typicality) {
            let innerArray = [];
            for (let innerKey in this.state.rule_typicality[key]) {
                innerArray.push({
                    concept: this.state.rule_typicality[key][innerKey]['rule_name'],
                    percentage_present: this.state.rule_typicality[key][innerKey]['percent_present'],
                    percentage_correct: this.state.rule_typicality[key][innerKey]['percent_correct'],
                    typicality: this.state.rule_typicality[key][innerKey]['typicality']
                });
            }
            rule_data.push({
                concept: key,
                innerArray: innerArray
            });
        }
        const size = 475;
        const imageSize = 325;
        /**
         * concept display
         */
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
                                 style={{width: (size * concept_data[i].percentage_correct * concept_data[i].percentage_present).toString() + "px"}}>
                                {(concept_data[i].percentage_correct * 100).toFixed(2).toString() + "%"}
                            </div>

                            <div className="conceptIncorrectBar"
                                 style={{width: (size * (concept_data[i].percentage_present - concept_data[i].percentage_correct * concept_data[i].percentage_present)).toString() + "px"}}>
                            </div>

                            <div className="restBar"
                                 style={{width: (size * (1 - (concept_data[i].percentage_present ))).toString() + "px"}}>
                            </div>
                        </div>
                        <br>
                        </br>
                        <div>
                            <div className="percentageOfTotalBar"
                                 style={{width: (size * concept_data[i].percentage_present).toString() + "px"}}>
                                {((concept_data[i].percentage_present) * 100).toFixed(2).toString() + "%"}</div>
                            <div className="pointer"></div>

                        </div>
                        <br>
                        </br>
                    </div>
            } )
        }

        const rule_data_view = [];
        /**
         * rule data display
         */
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
                                <div className="ruleCorrectBar" style={{width: (size * rule_data[i].innerArray[e].percentage_correct * rule_data[i].innerArray[e].percentage_present).toString() + "px"}}>
                                </div>

                                <div className="ruleInCorrectBar" style={{width: (size * (rule_data[i].innerArray[e].percentage_present - rule_data[i].innerArray[e].percentage_correct * rule_data[i].innerArray[e].percentage_present)).toString() + "px"}}>
                                </div>

                                <div className="restBar" style={{width: (size * (1 - (rule_data[i].innerArray[e].percentage_present ))).toString() + "px"}}>

                                </div>
                            </div>
                            <br>
                            </br>
                            <div>
                                <div className="percentageOfTotalBar" style={{width: (size * rule_data[i].innerArray[e].percentage_present).toString() + "px"}}>
                                    {(rule_data[i].innerArray[e].percentage_present * 100).toFixed(2).toString() + "%"}</div>
                                <div className="pointer"></div>

                            </div>
                            <br>
                            </br>
                        </div>
                })
            }

        }
        console.log(rule_data_view)

        let typicality_view = []
        /**
         * typicality display
         */
        for(let i = 0; i < this.state.typicalities; i++){
            typicality_view.push(<div>
                <div className={"everything"}>

                    <div className={"left-of-charts"}>
                        <div className={"main-wrap"}>
                            <div className={"left"}>
                                <h2>Concepts</h2>
                                <h4>Legend:</h4>
                                <div className={"main-wrap"}>
                                    <p id={"conceptP1"}>Percentage of correct predictions among concept-associated images</p>
                                    <p id={"conceptP2"}>Percentage of concept-associated images in dataset</p>
                                </div>
                                <label>Sort by: </label>
                                <Select id={"selectFilter"} dropdownMatchSelectWidth={false} onChange={this.sortConceptsByFilter}>
                                    <Option value={'typicality'}>Typicality</Option>
                                    <Option value={'percent_present'}>Percentage present</Option>
                                </Select>
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
                                <h2>Rules</h2>
                                <h4> </h4>
                                <div className={"main-wrap"}>
                                    <p id={"ruleP1"}>Percentage of correctly classified images within rule-associated images</p>
                                    <p id={"ruleP2"}>Percentage of concept-associated images among images with the predicted class</p>
                                </div>
                                <label>Sort by: </label>
                                <Select id={"selectFilter"} dropdownMatchSelectWidth={false} onChange={this.sortRulesByFilter}>
                                    <Option value={'typicality'}>Typicality</Option>
                                    <Option value={'percent_present'}>Percentage present</Option>
                                </Select>
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
            </div>)
        }


        let classesInput = []
        /**
         * typicality header display
         */
        if(this.state.typicalities === -1 || this.state.confusion_matrix === -1){
            document.getElementById("placeholder").innerHTML = "There was not any data available to match your search"
        }else{

            if(this.state.numClasses > 0) {
                classesInput.push(<div><Button onClick={this.addClassInput}>+</Button><Button onClick={this.removeClassInput}>-</Button></div>)
            }
            for(let i = 0; i < this.state.numClasses; i++){
                classesInput.push(<div>
                    <Input id={"classesInput" + i} placeholder={(i + 1) + ". class to add"}/>
                </div>)
            }
        }

        return (
            <div id="QueryClassificationFormulas">
                <div class="errorDiv">
                </div>
                <div id={"QueryParams"}>
                    <div id={"selectGroup"}>
                        <label id={"label1"}>Query Concept</label>
                        <Input style={{width: 200, textAlign: 'center', height: 30}} placeholder="Concept 1" id={"concept0"}/>
                        <Button onClick={this.onAddChild} id={"addConceptButton"}>+ add concept</Button>
                        <Button onClick={this.onRemoveChild} id={"removeConceptButton"}>- remove concept</Button>
                        <div id={"extraConcepts"}>
                            {conceptList}
                        </div>
                    </div>

                    <Button onClick={this.getConfusionMatrix} id={"MatrixBtn"} style={{width: 200}}>Show Confusion Matrix</Button>
                    <Button onClick={this.getTypicalityScore} id={"ScoreBtn"} style={{width: 200}}>Show Typicality Score</Button>

                </div>
                <div id={"Settings"}>
                    <h2 id={"settingTitle"}>Settings:</h2>
                    <label>Input antecedent length</label>
                    <Slider min={0} max={10} step={1} defaultValue={3} onChange={
                        (value) => {
                            this.setState({
                                antecedent : value
                            });
                        }
                    }/>
                    <span id={"radios"}>
                        <div id={"imagesSettings"}>
                            <h3 className={"querySettingTitle"}>Set of images considered for the computations</h3>
                            <Radio.Group id={"imagesSettingsGroup"} onChange={this.changeImageSet} defaultValue={1}>
                                <Radio value={1}>All images</Radio>
                                <Radio value={2}>Only images with correct classification</Radio>
                                <Radio value={3}>Only images with incorrect classification</Radio>
                            </Radio.Group>
                        </div>
                        <div id={"ClassificationTaskSettings"}>
                            <h3 className={"querySettingTitle"}>Computation task</h3>
                            <Radio.Group id={"ClassificationTaskSettingsGroup"} defaultValue={1}>
                                <Radio value={1} onChange={this.deselectedSelection}>All classes</Radio>
                                <Radio value={2} onChange={this.selectedSelection}>Class selection</Radio>
                                {classesInput}
                            </Radio.Group>
                        </div>
                    </span>
                </div>
                <div id={"placeholder"}/>
                {confusionMatrix}
                {typicality_view}
            </div>
        );
    }
}

export default QueryClassificationFormulas;
