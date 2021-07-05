import React from 'react';
import "../css/AboutInterface.less"
const URL = "http://localhost:3000"

class AboutInterface extends React.Component {

    //all texts are loaded from this data array
    data = {
        'page_title' : 'Explainability Tool',
        'intro' : 'This tool allows to explore and explain the behaviour of machine learning model by integrating SECA (SEmandic Concept Extraction and Analysis) method. The interface allows the following analysis actions',
        'titles': ['confusion matrix', 'explore', 'wiki', 'query'],
        'texts' : ['Understand the distribution of correctly and wrongly predicted images, once you select the ground truth-prediction combination of your choice you can analyze the concepts and rules used by the model to make Such prediction. This interface also allows you to see if the conceps used are correct or wrong both in correct predictions and wrong predictions',
                   'This interface allows you to have a global overview of the concepts and rules that are manly used by the model',
                   'Learn what input experts gave about a specific topic and what concepts and rules they believe the model should rely on.',
                   'Do you have a specific case of concepts or rules used by the model? Do you want to check the belonging of a rule to a specific class? This interface allows you to submit a specific query of rules, search for images belonging to a specific classification or submit a new image to classify']
    }

    render() {
    //more can be added by adding their tab number to the tabs list below and adding them to data above
        let tabs = ['3', '4','6','5']
        let html = []
        for(let i = 0; i < this.data['titles'].length; i++){
            html.push(  <div className = "section" id={"section" + i}>
                            <a href={URL + "/home/?tab=" + tabs[i]}>
                                <h1 className="sectionTitle">{this.data['titles'][i]}</h1>
                            </a>
                            <p>{this.data['texts'][i]}</p>
                        </div>);
        }
//{html}
        return (
            <div id={"aboutInterface"}>
                <h2>{this.data['page_title']}</h2>
                <p>{this.data['intro']}</p>
                <div className="wrapper"> {html} </div>

            </div>
        );
    }
}

export default AboutInterface;