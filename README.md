Readme file not finished yet!

# Community-based Abuse Detection

In this repository you will find the code for the Master's Thesis: "Community-based Abuse Detection: Using Distantly Supervised Data and Biased Word Embeddings".

The goal of this thesis is to find out whether data coming from abusive communities and other non-abusive communities can be used for the detection of abusive language. 
The community-based data are collected from hateful communities and 'normal' subreddits on Reddit. With this data, we create distant datasets and generate task-specific polerized embeddings which are used to train abuse detection models. These models are tested both on an in-domain test set created in this research and on existing cross-domain test sets. 
This study confirms that data coming from abusive and non-abusive communities can be used for the detection of abusive language. The results indicate that models learn to classify abuse from silver distant training data (even though they still get outperformed by smaller gold training data). Furthermore, models that use pre-trained biased abusive embeddings generated from this data are showing competitive results when compared against much larger pre-trained generic embeddings.

# Data Statement ([Bender and Friedman, 2018](https://www.mitpressjournals.org/doi/abs/10.1162/tacl_a_00041))

Data in the Gold Reddit test set has been collected from the medium Reddit and the language of the messages is English. The annotation of the explicit, implicit and non-abusive labels have been conducted by a group of first-year Information Science Bachelor students and the author of this paper. The annotators group consisted of 31 men and 10 women. Out of this group 21 students have previous experience with annotating documents and 19 students did not have any previous experience. The average age is 21.025 years and ranges between the ages of 18 and 42. All annotators have the Dutch nationality. 

All ages refer to the time of annotation: April 2020.


# Repository structure

### README.md
Description of the repository.
### requirements.txt
Required Python packages necessary for running the program.

### /annotations
Folder that contains code to create and extract annotated data by annotators.
### /annotations/output/
Folder that contains outputfiles of student annotations.
### /annotations/build_student_group_files.py
Creates annotation data for groups of students with common and individual messages.
### /annotations/collect_test_comments_students.py
Extracts test comments from Reddit archive files.
### /annotations/evaluate_students_annotations.py
Combines all annotations and calculates fleiss kappa within groups of annotators, writes final labels to output/

### /collection/extract_non_abusive
Folder that contains code to extract non-abusive messages from Reddit archive files.
### /collection/extract_non_abusive/collect_non-abusive_messages.py
Code to extract non-abusive messages from Reddit archive files.
### /collection/extract_non_abusive/expandedLexicon.txt
Lexicon used to filter explicit messages from abusive communities
### /collection/extract_non_abusive/subreddit_statistics.tsv
List of abusive communities

### /data
Folder that contains training and test data for the project
### /data/training/
Folder that contains training data
### /data/training/batches
Folder that contains the distant training data with 25-25-50 and 33-33-33 distributions of labels
### /data/training/gold_train
Folder that contains the gold training data files: AbusEval and OffensEval2019
### /data/test
Folder that contains all test data for the experiments

