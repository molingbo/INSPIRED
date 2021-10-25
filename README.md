# INSPIRED: Dataset for Interactive Semantic Parsing for Knowledge-Based Question Answering (KBQA)

Existing studies on semantic parsing focus primarily on mapping a natural-language utterance to a corresponding logical form in one turn. However, because natural language can contain a great deal of ambiguity and variability, this is a difficult challenge. In this work, we investigate an interactive semantic parsing framework that explains the predicted logical form *step by step* in natural language and enables the user to make corrections through *natural-language feedback* for individual steps. We focus on question answering over knowledge bases (KBQA) as an instantiation of our framework, aiming to increase the transparency of the parsing process and help the user appropriately trust the final answer.  To do so, we construct ***INSPIRED***, a crowdsourced dialogue dataset derived from the **ComplexWebQuestions** dataset.

This repository will contain the dataset and code for our paper [Towards Transparent Interactive Semantic Parsing via Step-by-Step Correction](https://arxiv.org/abs/2110.08345).

## Data
### Dataset Download
> The dataset can be downloaded under this path: `./data/dataset.jsonl`

### Data Structure
> In the dataset file, each line is a dictionary with several keys:

```json
{
    "id": "ID number",
    "cwq_question": "Original complex question in CWQ dataset",
    "rephrased_question": "Rephrased complex question by workers",
    "rephrased_question_label": " 'Replacement' or 'Alternative' ",
    "question": "If rephrased_question_label is marked as 'Replacement', set the value the same as rephrased_question; Otherwise, set it the same as cwq_question",
    "final_answer": "Final answer for the complex question",
    "gold_parse": "Gold sparql query for complex question",
    "preprocessed_gold_parse": "Preprocessed gold parse with entities and prefix replaced",
    "predicted_parse": "Predicted sparql query by initial semantic parser",
    "gold_sub_lfs": "A list of gold sub-logical forms after decomposition",
    "pred_sub_lfs": "A list of predicted sub-logical forms after decomposition",
    "gold_sub_qs": [
        {
          "sub_id": "ID of sub questions",
          "sub_question": "Rephrased sub question",
          "temp_sub_question": "Templated sub question for gold sub-logical form",
          "answer": "Answer for each sub question",
        }, "..."], 
    "pred_sub_qs": [
        {
          "sub_id": "ID of sub questions",
          "sub_question": "Rephrased sub question",
          "temp_sub_question": "Templated sub question for predicted sub-logical form",
          "answer": "Answer for each sub question",
        }, "..."], 
    "feedback": "A list of human feedback"
    
}
```
