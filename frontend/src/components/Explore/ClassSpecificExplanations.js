import React, {useState, useEffect} from "react";
import 'antd/dist/antd.css';
import '../../css/ClassSpecificExplanations.css';
import axios from "axios";
import {data_specific_explanations_url, data_specific_explanations_more_complete_url} from "../../API"

import { Radio, Slider, Button, Table } from "antd";
const RadioGroup = Radio.Group;

function ClassSpecificExplanations() {
//    var rules = []
//    var supp_conf = []
    const [table, setTable] = useState({});
    const [image_setting, set_image_setting] = useState([""]);
    const [rule_score, set_rule_score] = useState("typicality");
    const [sorting, setSorting] = useState("alphabetical");
    const [session_id, setSession] = useState(JSON.parse(sessionStorage.getItem("session")))
    const [token, setToken] = useState(
        JSON.parse(sessionStorage.getItem("token"))
    );
    const fetchData = (event) => {
        const errorDiv = document.getElementsByClassName("errors")[0]
        axios
          .post(data_specific_explanations_url,
          JSON.stringify({ IMAGE_SET_SETTING: image_setting, "session_id" : session_id }), {
            headers: {
                "Content-Type": "application/json",
                Authorization: "Token " + token,
            },

         })
          .then(function (response) {

            setTable(response.data["data"]);
            update()
          })
          .catch(function (error) {
            errorDiv.innerHTML = ""
            const e = document.createElement("div")
            e.className = "error"
            e.innerHTML = "Something went retrieving the statistics. Try again later. Consult the documentation if necessary."
            errorDiv.appendChild(e)
          });

          // Run a second time with more complete explanations.
          axios
          .post(data_specific_explanations_more_complete_url,
          JSON.stringify({ IMAGE_SET_SETTING: image_setting, "session_id" : session_id }), {
            headers: {
                "Content-Type": "application/json",
                Authorization: "Token " + token,
            },

         })
          .then(function (response) {

            setTable(response.data["data"]);
            update()
          })
          .catch(function (error) {
            errorDiv.innerHTML = ""
            const e = document.createElement("div")
            e.className = "error"
            e.innerHTML = "Something went retrieving the statistics. Try again later. Consult the documentation if necessary."
            errorDiv.appendChild(e)
          });
    };


    const [support, setSupport] = useState(0);
    const [confidence, setConfidence] = useState(0);
    const [data, setData] = useState([]);

    const columns = [
        {
            title: "section",
            dataIndex: "section",
        }
    ]
    useEffect(() => {update();}, [confidence, support, rule_score, sorting, table])

    // sorting the fetched data
    function sortAlphabetical(array) {

        const orderedKeys = []

        for (var item in array) {
            orderedKeys.push(item)
        }

        return orderedKeys.sort()
    }

    // sorting the fetched data on given category
    function sort(array, on) {
        var index = 0
        if (on === "alphabetical") {
            return sortAlphabetical(array)
        }
        else if (on === "support") {
            index = 0
        }
        else if (on === "confidence") {
            index = 1
        }
        else if (on === "present_percentage") {
            index = 2
        }
        else if (on === "correct_percentage") {
            index = 3
        }
        else if (on === "typicality") {
            index = 4
        }

        const orderedKeys = []

        for (var item in array) {
            orderedKeys.push(item)
        }

        for (let i = 0; i < orderedKeys.length; i++) {

            var min_idx = i;
            for (let j = i + 1; j < orderedKeys.length; j++) {

                if (array[orderedKeys[j]][index] < array[orderedKeys[min_idx]][index]) {
                    min_idx = j;

                }
            }
            [orderedKeys[min_idx], orderedKeys[i]] = [orderedKeys[i], orderedKeys[min_idx]]
        }
        return orderedKeys
    }
    function update() {

        const arr = []

        for (var key in table) {

            const ruleString = []
            const sortedTable = sort(table[key], sorting)
            for (var rule in sortedTable) {
                if (table[key][sortedTable[rule]][0] > support && table[key][sortedTable[rule]][1] > confidence) {
                    var subText = ""
                    if (rule_score === "typicality") {
                        subText = "typicality: " + parseFloat(table[key][sortedTable[rule]][4]).toFixed(2)
                    }
                    if (rule_score === "present_percentage") {
                        subText = "percentage among images: " + (parseFloat(table[key][sortedTable[rule]][2])*100).toFixed(2) + "%"
                    }
                    if (rule_score === "correct_percentage") {
                        subText = "correct percentage: " + (parseFloat(table[key][sortedTable[rule]][3])*100).toFixed(2) + "%"
                    }

                    ruleString.push({
                        view:
                            <p className={"ruleEntryP"}>
                                <p className={"ruleEntry"}>
                                    {sortedTable[rule] + ", "}
                                </p>
                                <div className={"hide"}>{subText}</div>
                            </p>
                    })
                }
            }
            arr.push({section:
                <div className={"tableEntry"}>
                    <h3>{key}</h3>

                    <div className={"ruleList"}>
                        {ruleString.map(item => (
                        <>
                           {item.view}
                        </>
                        ))}
                    </div>
                </div>
            })

        }
        setData(arr)
    }
    const userUpdatedSetting = (event) => {
        set_image_setting(event.target.value);
    };
    return (
    <div>
      <div className="errors">
      </div>
      <p>In class specific explanations</p>

      <div className="leftSide">
      <Table columns={columns} dataSource={data} />
      </div>
      <div className="rightSide">
        <div className="scores">
            <div className="subtitle"><h1>scores</h1></div>

            <RadioGroup onChange={(event) => {
                set_rule_score(event.target.value);

                update()
                }
            }>
                <Radio value={"typicality"}>Rule typicality</Radio><br/>
                <Radio value={"present_percentage"}>Percentage of concept-associated images among images with the predicted class</Radio><br/>
                <Radio value={"correct_percentage"}>Percentage of correctly classified images within rule-associated images</Radio><br/>
            </RadioGroup>

        </div>

        <div className="filters">
            <div className="subtitle"><h1>filter</h1></div>
            <div className="slider">Support filter <Slider min={0} max={1} step={0.01} onChange={
                (value) => {
                    setSupport(value);
                    update();
                }
            }/></div>
            <div className="slider">Confidence filter <Slider max={1} min={0} step={0.01} onChange={
                (value) => {
                    setConfidence(value);
                }
            }/></div>
        </div>

        <div className="sort">
            <div className="subtitle"><h1>order of representation</h1></div>


            <RadioGroup onChange={(event) => setSorting(event.target.value)}>
                <Radio value={"alphabetical"}>Alphabetical order</Radio><br/>
                <Radio value={"support"}>Support</Radio><br/>
                <Radio value={"confidence"}>Confidence</Radio><br/>
                <Radio value={"typicality"}>Typicality</Radio><br/>
                <Radio value={"present_percentage"}>Percentage of concept-associated images among images with the predicted class</Radio><br/>
                <Radio value={"correct_percentage"}>Percentage of correctly classified images within rule-associated images</Radio><br/>
            </RadioGroup>
        </div>

        <div className="settings">
            <div className="subtitle"><h1>settings</h1></div>
            The set of images considered for the computation<br/>
            <RadioGroup onChange={userUpdatedSetting}>
                <Radio value={"ALL_IMAGES"}>All images</Radio><br/>
                <Radio value={"CORRECT_PREDICTION_ONLY"}>Only images with correct predictions</Radio><br/>
                <Radio value={"WRONG_PREDICTION_ONLY"}>Only images with incorrect predictions</Radio><br/>
            </RadioGroup>
            <br/>

        </div>
        <Button onClick={fetchData}>Search</Button>
      </div>
    </div>
  );
}

export default ClassSpecificExplanations;
