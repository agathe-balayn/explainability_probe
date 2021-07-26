import React from 'react';
import "../css/AboutInterface.less"
const URL = "http://localhost:3000"

class AboutInterface extends React.Component {

    //all texts are loaded from this data array
    data = {
        'page_title' : 'Explainability Tool',
        'intro' : 'This tool allows to explore and explain the behaviour of machine learning model by integrating SECA (SEmandic Concept Extraction and Analysis) method. The interface allows the following analysis actions',
        'titles': ['Dashboard', 'Overview through confusion matrix', 'Overview through main concepts', 'wiki', 'query'],
        'texts' : ['Do you want to take a glance at your models? And look at its main behaviours? This interface gives you a brief overview of the model, each functionality being further expanded in the other tabs.',
                    'Understand the distribution of correctly and wrongly predicted images. Once you select the ground truth-prediction combination of your choice, you can analyze the concepts and rules used by the model to make such prediction, as well as the corresponding images. This interface also allows you to see if the conceps used are correct or wrong both in correct predictions and wrong predictions',
                   'This interface allows you to have a global overview of the concepts and rules that are manly used by the model',
                   'Learn what input experts gave about a specific class and what concepts and rules they believe the model should rely on.',
                   'Do you have a specific case of interest for concepts or rules used by the model? Do you want to check the belonging of a concept to a specific class? This interface allows you to submit a specific query of concepts or rules and learn about it, and to search for images belonging to a specific class or with specific concepts.']
    }

    render() {
    //more can be added by adding their tab number to the tabs list below and adding them to data above
        let tabs = ['1', '3', '4','6','5']
        let html = []
        for(let i = 0; i < this.data['titles'].length; i++){
            html.push(  <div className = "section" id={"section" + i }>
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