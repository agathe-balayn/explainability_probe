import React from 'react';
import shark_example_annotated_image from './../images/shark_example_annotated_image.png'
import shark_example_original_image from './../images/shark_example_original_image.png'
import { Layout } from 'antd';
import "../css/AboutSeca.less"

const { Content } = Layout;

class AboutSECA extends React.Component {

    //all texts are loaded from this data array
    data = {
        'main_title' : 'About SECA',
        'intro' : 'SECA is a scalable human-in-the-loop approach for global interpretability. Salient image areas identified by local interpretability methods are annotated with semantic concepts, which are then aggregated into a structured representation of images to facilitate automatic statistical analysis of model behaviour',
        'title' : 'fundamental concepts:',
        'titles': ['Saliency map', 'Classification', 'Rule', 'Concept', 'Typicality score'],
        'texts' : ['A method that highlights the most important, or most sensitive, pixels for the decision with respect of a specific class (activation function for that class for each image pixel',
                    'Categorization done by the model into a specific class based on the Rules it has detected',
                    'Combination of concepts within a category',
                    'Observable properties within areas of the saliency maps',
                    ' Degree of association between concepts appeasing in images and the classification labels that the ML model assigns to them']
    }

    render() {

        let texts = []
        for(let i = 0; i < (this.data)['titles'].length; i++) {
            texts.push(
                <tr>
                    <th>
                        <h3 className="concepts_titles"> {this.data['titles'][i]} </h3>
                    </th>
                    <td>
                        <p> {this.data['texts'][i]} </p>
                    </td>
                </tr>)
        }

        return (
            <Layout>
                <Layout>
                    <Content>
                        <h2>{this.data['main_title']}</h2>
                        <div id='intro' className={"topPartSeca"}><p> {this.data['intro']} </p></div>
                        <img src={shark_example_annotated_image} className={"topPartSeca"} alt={""}/>
                        <img src={shark_example_original_image} className={"topPartSeca"} alt={""}/>
                    </Content>
                </Layout>
                <h1>{this.data.title}</h1>
                <table id="concepts_table">{texts}</table>
            </Layout>
        );
    }
}

export default AboutSECA;