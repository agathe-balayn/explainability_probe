import React, { useEffect, useState } from "react";
import { Table, Radio, Button } from "antd";
import axios from "axios";
import { data_overall_explanations as data_url } from "../../API";
import "../../css/OverallExplanation.less";

const RadioGroup = Radio.Group;

function OverallExplanations() {
  const size = 300;
  const [image_setting, set_image_setting] = useState(["ALL_IMAGES"]);
  const [concept_data, set_concept_data] = useState({});
  const [table_data, set_table_data] = useState([]);
  const [sorting, setSorting] = useState("typicality");
  const [session_id, setSession] = useState(JSON.parse(sessionStorage.getItem("session")))
  const [token, setToken] = useState(JSON.parse(sessionStorage.getItem("token")));

  const columns = [
    {
      title: "antecedent",
      dataIndex: "antecedent",
    },
    {
      title: "statistics",
      dataIndex: "statistics",
    },
  ];

    // Function that sorts the entries in the fetched data.
  function sort(array, on) {
    if (on === "alphabetical") {
        for (let i = 0; i < array.length; i++) {

            var min_idx = i;
            for (let j = i + 1; j < array.length; j++) {

                if (array[j]["antecedent"] < array[min_idx]["antecedent"]) {
                    min_idx = j;

                }
            }
            [array[min_idx], array[i]] = [array[i], array[min_idx]]
        }
    }
    else {
        for (let i = 0; i < array.length; i++) {

            var min_idx = i;
            for (let j = i + 1; j < array.length; j++) {

                if (array[j][on] > array[min_idx][on]) {
                    min_idx = j;

                }
            }
            [array[min_idx], array[i]] = [array[i], array[min_idx]]
        }
    }

    return array
  }
  useEffect(() => {
    const formatted_concepts = formatConceptData(concept_data);
    const table_data = make_table_data(sort(formatted_concepts, sorting));
    set_table_data(table_data);
  }, [concept_data, sorting]);

  const make_table_data = (formatted_concepts) => {
    var data = [];
    for (var i = 0; i < formatted_concepts.length; i++) {
      console.log(formatted_concepts[i])
      data.push({
        antecedent: formatted_concepts[i].antecedent,
        statistics: (
          <div>
            <div
              style={{
                height: "20px",
                alignItems: "center",
                display: "flex",
                marginBottom: "5px",
              }}
            >
              <div
                className="typicality"
                style={{
                  minHeight: "5px",
                  width:
                    (size * formatted_concepts[i].typicality).toString() + "px",
                  backgroundColor: "#999999",
                  float: "left",
                }}
              ></div>
              <div
                className="typicalityText"
                style={{ marginLeft: "5px", float: "left" }}
              >
                typicality: {formatted_concepts[i].typicality}
              </div>
            </div>

            <div
              className="correctBar"
              style={{
                minHeight: "20px",
                width:
                  (size * formatted_concepts[i].percentage_correct * formatted_concepts[i].percent_present).toString() +
                  "px",
                backgroundColor: "#7CFC00",
                display: "inline-block",
                float: "left",
              }}
            ></div>
            <div
              className="falseBar"
              style={{
                minHeight: "20px",
                width:
                  (size * formatted_concepts[i].percent_present * formatted_concepts[i].percentage_wrong).toString() +
                  "px",
                backgroundColor: "#FF0000",
                display: "inline-block",
                float: "left",
              }}
            ></div>

            <div
              className="restBar"
              style={{
                minHeight: "20px",
                width:
                  (
                    size *
                    (1 -formatted_concepts[i].percent_present)
                  ).toString() + "px",
                backgroundColor: "#D3D3D3",
                display: "inline-block",
                float: "left",
              }}
            >{"In dataset: " + ((formatted_concepts[i].percent_present) * 100).toPrecision(2).toString() + "%"}</div>
            <div style={{float: "left" }}>

                <dl style={{ marginTop: "10px" }}>

                  <dt class="green"></dt>
                  <p>{formatted_concepts[i].percentage_correct.toPrecision(2).toString() + "%"}</p>
                  <dt class="red"></dt>
                  <p>{formatted_concepts[i].percentage_wrong.toPrecision(2).toString() + "%"}</p>
                </dl>
              </div>
            
          </div>
        ),
      });
    }
    return data;
  };

  const formatConceptData = (concept_data) => {

    var formatted_data = [];
    const keys = Object.keys(concept_data);
    const values = Object.values(concept_data);

    for (var i = 0; i < keys.length; i++) {
      console.log("data")
    console.log(values[i])
      const table_entry = {
        antecedent: keys[i],
        typicality: values[i].typicality,
        percentage_correct: values[i].percent_correct,
        percent_present: values[i].percent_present,
        percentage_wrong: 1 - values[i].percent_correct,
      };
      formatted_data.push(table_entry);
    }
    return formatted_data;
  };

  const fetchData = (event) => {
    const errorDiv = document.getElementsByClassName("errorDiv")[0]
    errorDiv.innerHTML = ""
    axios
      .post(data_url, JSON.stringify({ IMAGE_SET_SETTING: image_setting, "session_id" : session_id }),
          {
              headers: {
                  "Content-Type": "application/json",
                  Authorization: "Token " + token,
              },
          })
      .then(function (response) {
        var data = response.data.result;
        console.log(data)
        set_concept_data(data["concepts"]);
      })
      .catch(function (error) {
        const e = document.createElement("div")
        e.className = "error"
        e.innerHTML = "Something went retrieving the statistics. Try again later. Consult the documentation if necessary."
        errorDiv.appendChild(e)
      });
  };

  const userUpdatedSetting = (event) => {
    set_image_setting(event.target.value);
  };

  return (
    <div>
      <div className="errorDiv">
      </div>
      <h1>Top Concepts</h1>
      <div className="leftSide">
        <Table
          locale={{ emptyText: "Please select a setting first!" }}
          columns={columns}
          dataSource={table_data}
        />
      </div>

      <div className="rightSide">
        <div className="sort">
            <div className="subtitle"><h1>order of representation</h1></div>
            <RadioGroup defaultValue="typicality" onChange={(event) => setSorting(event.target.value)}>
                <Radio value={"alphabetical"}>Alphabetical order</Radio><br/>
                <Radio value={"typicality"}>Typicality</Radio><br/>
                <Radio value={"percent_present"}>Percentage of concept-associated images</Radio><br/>
                <Radio value={"percentage_correct"}>Percentage of correct predictions</Radio><br/>
                <Radio value={"percentage_wrong"}>Percentage of wrong predictions</Radio><br/>
            </RadioGroup>
        </div>

        <div className="settings">
          <div className="subtitle">
            <h1>settings</h1>
          </div>
          The set of images considered for the computation
          <br />
          <RadioGroup defaultValue="ALL_IMAGES" onChange={userUpdatedSetting}>
            <Radio value={"ALL_IMAGES"}>All images</Radio>
            <br />
            <Radio value={"CORRECT_PREDICTION_ONLY"}>
              Only images with correct predictions
            </Radio>
            <br />
            <Radio value={"WRONG_PREDICTION_ONLY"}>
              Only images with incorrect predictions
            </Radio>
            <br />
          </RadioGroup>
          <br />
          <Button onClick={fetchData}>Search</Button>
        </div>
        
      </div>
    </div>
  );
}

export default OverallExplanations;
