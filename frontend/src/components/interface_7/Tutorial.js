import React from 'react'
import ReactPlayer from "react-player";


function Tutorial() {
    let tutorialTexts = [
        {
            "title": "Dashboard tab",
            "content": [{
                "questions": "“What is the behavior of the model for a specific class? Why are instances A and B given the same prediction? What is the commonality of concepts across two classes? What are the differences?”",
                "how_to": "view the overall behavior of the model across the confusion matrix and, at the same time, compare the use of the concepts in one or two classes with the use of concepts in other classes by querying a possible comparison. "
            }]
        },
        {
            "title": "Explore tab",
            "content": [{
                "questions": "“What are the rules used by the model with the most incidence for a specific classification? What are the concepts the model relies on generally?” ",
                "how_to": "You can view this information through the lists in the explore tab classification specific or related to the top 10 rules used by the model."
            }]
        }, {
            "title": "Confusion matrix tab",
            "content": [{
                "questions":
                    "“What are the ground truth and prediction combinations where " +
                    "the model makes the most mistakes? Where are predictions mostly correct? How are " +
                    "the misclassification distributed across the dataset? How much data like this" +
                    " is the system trained on? In what situations is the system likely to be correct/incorrect? Fo" +
                    "r these different cases, what kind of concepts does the model use to make predictions? Do they seem relevant?"
                ,
                "how_to":
                    "First identify erroneous or correct groups of predictions. If you want t" +
                    "o view data and concepts used within these groups, click on a cell of the matrix."
            }]
        },
        {
            "title": "Query tab",
            "content": [
                {
                    "questions":
                        "“What are images where the model has used the concept A? Which classes does the concept A lead to? What is the prediction for a class when concept A is missing from the image?”",
                    "answer":
                        "Answer these typologies of questions by querying a concept within the dataset or a concept related to a specific outcome."
                },
                {
                    "questions":
                        "“What is the incidence of a feature on the classification? How does the incidence of a feature for one class compare within other classes? Is the model using feature X in the way I expect it to? Does the model use feature X for its predictions?”"
                    , "answer":
                        "You can search for the strength of specific concepts, that can serve to compare these concepts to others you have identified using the tool. It can also serve to check whether behaviors you believe should be or not verified by the model, have been learned.",
                }, {
                    "questions":

                        "“Can the system predict edge cases?”"
                    ,
                    "answer":
                        "You can search for specific concepts/ combinations of concepts, how they are distributed among the images and which predictions they receive. That can allow you to understand further why an explanation has a high or low score in the other pages."
                }
            ]
        },
        {
            "title": "Wiki tab",
            "content": [{
                "questions":
                    "“What do experts rely on to identify these classes? What are edge cases I should check for?”",
                "how_to":
                    "You can come to this tab when you want to understand what the desirable concepts for each class are, and you can look at the information given by domain experts. You can then compare that to the model concepts within the remaining tabs."
            }]
        }
    ]
    let rows = []
    for (let i = 0; i < tutorialTexts.length; i++) {
        rows.push(
            <h1>{tutorialTexts[i]['title']}</h1>
        )
        for (let j = 0; j < tutorialTexts[i]['content'].length; j++) {
            rows.push(
                <div>
                    <p>Questions you may have: {tutorialTexts[i]['content'][j]['questions']}</p>
                    <p>{tutorialTexts[i]['content'][j]['how_to'] && "How to use the tab: "}{tutorialTexts[i]['content'][j]['how_to']}</p>
                    <p>{tutorialTexts[i]['content'][j]['answer']}</p>
                </div>)
        }
    }

    return (
        <div id={"tutorialInterface"}>
            <h2>How to use this interface</h2>
            <h1>Video explanation</h1>
            <div id={"tutorial"}>
                <p>Please watch this tutorial on YouTube to learn how to use this interface!</p>
                <ReactPlayer url="https://www.youtube.com/watch?v=lzI71r-UnbU" controls={true}/>
            </div>
            <h1>Here are some potential uses for each tab of the interface</h1>
            {rows}
        </div>
    )
}

export default Tutorial
