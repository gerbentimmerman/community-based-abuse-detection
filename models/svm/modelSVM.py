#!/usr/bin/python3
# General imports
import pandas as pd 
import numpy as np
import fasttext
import sys
import csv
import datetime
import pickle
from os import walk



# Preprocessing
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical
from nltk.tokenize import TweetTokenizer

# Data preperation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, KFold

# Model Building
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

# Saving model
from joblib import dump, load

# Evaluation
from sklearn.metrics import classification_report, accuracy_score



"""
################# Load training and test data
"""
def loadTrainingData(data_source, distribution, batch_train_file, gold_train_file, classification_type):
	"""
	Load in the training data based on classification_type and data_source
	"""

	# Map explicit and implicit to 0,1 if classification_type == binary
	if classification_type == 'binary':
		mapping_dict = {'NOT': 0, 'IMP' : 1, 'EXP' : 1, '0': 0, '1': 1, '2': 1}
	# Else multi-class classification
	else:
		mapping_dict = {'NOT': 0, 'IMP' : 1, 'EXP' : 2, '0': 0, '1': 1, '2': 2}


	if data_source == "reddit_distant" or data_source == 'reddit+gold':
		# Get training data
		datafile = "../../data/training/batches/{}/batch_train_{}.csv".format(distribution, batch_train_file)
		reddit_df = pd.read_csv(datafile, names=['id', 'subreddit', 'text', 'classes'], sep='\t', header=0, index_col=0, error_bad_lines=False)
		reddit_df.dropna(inplace=True)
		
		reddit_df['labels'] = reddit_df['classes'].apply(lambda x: mapping_dict[str(x)])

	if data_source == "gold_train" or data_source == 'reddit+gold':
		goldtrain_df = pd.read_csv(gold_train_file, names=['id', 'text', 'classes'], sep='\t', header=0, index_col=0, error_bad_lines=False)
		goldtrain_df.dropna(inplace=True)
		
		goldtrain_df['labels'] = goldtrain_df['classes'].apply(lambda x: mapping_dict[str(x)])

	print("##### Loaded in training data #####", file=text_file)
	
	# Decide which data to return
	if data_source == 'reddit+gold':
		# Combine reddit + gold data
		reddit_gold_df = reddit_df.append(goldtrain_df, ignore_index=True).reset_index()
		return reddit_gold_df[['text', 'labels']]

	if data_source == 'reddit_distant':
		return reddit_df[['text', 'labels']]
	else:
		return goldtrain_df[['text', 'labels']]


	
	


def loadTestData(classification_type):
	test_dict = {}
	test_dict['offenseval2019'] = pd.read_csv("../../data/test/test_offenseval2019.csv", names=['id', 'text', 'classes'], sep='\t', header = 0)
	test_dict['abuseval'] = pd.read_csv("../../data/test/test_abuseval.csv", names=['id', 'text', 'classes'], sep='\t', header = 0)
	test_dict['offenseval2020'] = pd.read_csv("../../data/test/test_offenseval2020.csv", names=['id', 'text', 'classes'], sep='\t', header = 0)
	#test_dict['hateval2019'] = pd.read_csv("../../data/test/test_hateval.csv", names=['id', 'text', 'classes'], sep='\t', header = 0)
	test_dict['reddit_students_self'] = pd.read_csv("../../data/test/test_students_self_reddit.csv", names=['id', 'text', 'classes', 'annotator'], sep='\t', header = 0, index_col=0)

	# Map explicit and implicit to 0,1 if classification_type == binary
	if classification_type == 'binary':
		mapping_dict = {'0': 0, '1' : 1, '2' : 1, '0.0': 0, '1.0' : 1, '2.0' : 1, 'NOT': 0, 'IMP' : 1, 'EXP' : 1}
	else:
		mapping_dict = {'0': 0, '1' : 1, '2' : 2, '0.0': 0, '1.0' : 1, '2.0' : 2, 'NOT': 0, 'IMP' : 1, 'EXP' : 2}
	
	for testset in test_dict.keys():
		test_dict[testset]['labels'] = test_dict[testset]['classes'].apply(lambda x: mapping_dict[str(int(x))])
	
	print("##### Loaded in test sets #####", file=text_file)
	return test_dict


"""
########################### Train SVM model
"""
def train_model(x_train, y_train, input_type):
	X = np.array(x_train)
	y = np.array(y_train)
	print("##### Training Model #####", file=text_file)
	if input_type == "tfidf":
		# Train the SVM classifier
		text_clf = Pipeline([('vect', TfidfVectorizer(ngram_range=(1,3))),
						  ('clf', SVC(C = 1.0)),
						  ])
		text_clf.fit(x_train, y_train)
		print(text_clf)
	
	elif input_type == "embeddings":
		text_clf = SVC(C=1.0)
		text_clf.fit(x_train, y_train)
		print(text_clf)

	print("############ Done training model #############", file=text_file)
	return text_clf


def cross_validation(x_train, y_train, input_type, test_dict):
	X = np.array(x_train)
	y = np.array(y_train)

	test_scores = {"distant252550": {"accuracy": 0, "macro-f1": 0}, "distant333333": {"accuracy": 0, "macro-f1": 0}, "cross_val": {"accuracy": 0, "macro-f1": 0}}
	print("##### Training Model #####")
	if input_type == "tfidf":
		# Initialize pipeline with tfidf vectorizer and svm classifier
		text_clf = Pipeline([('vect', TfidfVectorizer(ngram_range=(1,3))),
						  ('clf', SVC(C = 1.0)),
						  ])
	elif input_type == "embeddings":
		# Initialize Classifier
		text_clf = SVC(C=1.0)

	n_splits = 5
	kf = KFold(n_splits)
	for train_index, test_index in kf.split(X):
		X_train, X_test_fold = X[train_index], X[test_index]
		y_train, y_test_fold = y[train_index], y[test_index]

		text_clf.fit(X_train, y_train)
		# Predict on test fold
		y_pred_fold = text_clf.predict(X_test_fold)

		print(classification_report(y_test_fold, y_pred_fold, digits=4), file=text_file)
		output_dict = classification_report(y_test_fold, y_pred_fold, digits=4, output_dict=True)
		test_scores['cross_val']['accuracy'] += output_dict['accuracy']
		test_scores['cross_val']['macro-f1'] += output_dict['macro avg']['f1-score']

		# Predict on distantly supervised testsets with different distributions
		for testset in test_dict.keys():
			print(len(test_dict[testset][0]), len(test_dict[testset][1]))
			X_test_distant, y_test_distant = test_dict[testset][0], test_dict[testset][1]
			y_pred_distant = text_clf.predict(X_test_distant)
			output_dict = classification_report(y_test_distant, y_pred_distant, digits=4, output_dict=True)
			test_scores[testset]['accuracy'] += output_dict['accuracy']
			test_scores[testset]['macro-f1'] += output_dict['macro avg']['f1-score']
	for testset in test_scores.keys():
		test_scores[testset]['macro-f1'] = test_scores[testset]['macro-f1'] / n_splits
		test_scores[testset]['accuracy'] = test_scores[testset]['accuracy'] / n_splits
		print("Macro-F1 avg {}: {}".format(testset, test_scores[testset]['macro-f1']), file=text_file) 
		print("Accuracy avg {}: {}".format(testset, test_scores[testset]['accuracy']), file=text_file)

	return test_scores


def evaluation(text_clf, x_test, y_test, classification_type, testset):
	print("############ Evaluating model #############")
	y_pred = text_clf.predict(x_test)

	# Convert labels to binary when trained on multiclass

	if classification_type == "binary":
		y_converted = []
		for i in y_pred:
			if i == 2:
				y_converted.append(1)
			else:
				y_converted.append(i)
		y_pred = y_converted
	else:
		if testset in ["offenseval2019", "offenseval2020", "hateval2019"]:
			y_converted = []
			for i in y_pred:
				if i == 2:
					y_converted.append(1)
				else:
					y_converted.append(i)
			y_pred = y_converted

	print(classification_report(y_test, y_pred, digits=4), file=text_file)
	result_dict = classification_report(y_test, y_pred, digits=4, output_dict=True)

	# Scoring
	#print(accuracy_score(y_test, y_pred))

	return result_dict






"""
####################### Creating embeddings for SVM
"""
def load_glove_embeddings(tokenizer, vocab_size):
	glove_dict = dict()
	with open('../../data/embeddings/glove/glove.840B.300d.txt', 'r', encoding='utf8' ) as f:
		for line in f:
			values = line.split(' ')
			try:
				word = values[:-300][0]
				vector = np.asarray(values[-300:], 'float32')
			except:
				continue
			glove_dict[word] = vector

	print('Loaded %s word vectors.' % len(glove_dict), file=text_file)

	glove_matrix = np.zeros((vocab_size, 300)) #Dimension vector in embeddings
	# Create embedding matrix word_idx: [1, 300]
	for word, index in tokenizer.word_index.items():
		if index > vocab_size - 1:
			break
		else:
			embedding_vector = glove_dict.get(word)
			if embedding_vector is not None:
				glove_matrix[index] = embedding_vector

	print("############ Done creating glove embeddings #############", file=text_file)
	return glove_dict, glove_matrix



def load_fasttext_embeddings(tokenizer, vocab_size):
	# /data/s2769670/scriptie/
	embeddings_na = fasttext.load_model("../../data/embeddings/fasttext/embeddings_non_abusive_1_2_300.model")
	embeddings_a = fasttext.load_model("../../data/embeddings/fasttext/embeddings_abusive_1_2_300_large.model")


	non_abusive_matrix = glove_matrix = np.zeros((vocab_size, 300)) #Dimension vector in embeddings
	abusive_matrix = np.zeros((vocab_size, 300)) #Dimension vector in embeddings
	combined_matrix = np.zeros((vocab_size, 600)) # Abusive + non_abusive embeddings

	for word, index in tokenizer.word_index.items():
		if index > vocab_size - 1:
			break
		else:
			embedding_vector_na = embeddings_na.get_word_vector(word)
			embedding_vector_a = embeddings_a.get_word_vector(word)
			if embedding_vector_na is not None:
				non_abusive_matrix[index] = embedding_vector_na
			if embedding_vector_a is not None:
				abusive_matrix[index] =  embedding_vector_a

			# Make matrix with 600 dimensions
			if embedding_vector_a is not None and embedding_vector_na is not None:
				combined_matrix[index] =  np.hstack((embedding_vector_na, embedding_vector_a))
	print('########## Loaded fasttext vectors #############', file=text_file)
	return non_abusive_matrix, abusive_matrix, combined_matrix



def sent_vectorizer(sent, model):
	sent_vec = []
	numw = 0
	for w in sent:
		try:
			if numw == 0:
				sent_vec = model[int(w)]
			else:
				sent_vec = np.add(sent_vec, model[int(w)])
			numw+=1
		except:
			pass
	
	#print(print(len(np.asarray(sent_vec, dtype=float))), np.asarray(sent_vec, dtype=float) / numw)
	if len(sent_vec) == 0:
		print(sent)
	sequence = np.asarray(sent_vec) / numw
	#print(sequence.shape)
	return sequence



def create_embeddings(x_train, embedding_source, experiment_number, model, existing_models, tokenizer_name):
	# Train the model
	if model not in existing_models:
		# Create sequences word -> indexes
		tokenizer = Tokenizer(oov_token='<UNK>')
		tokenizer.fit_on_texts(x_train)
		with open("../models_saved/svm/exp{}/tokenizers/{}".format(experiment_number, tokenizer_name), 'wb') as handle:
				pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
		print("Training new model!")
	# Load existing model
	else:
		with open("../models_saved/svm/exp{}/tokenizers/{}".format(experiment_number, tokenizer_name), 'rb') as handle:
			tokenizer = pickle.load(handle)
		vocab_size = len(tokenizer.word_index) + 1
		print("Loading old model!")


	# Get vocabulary size 
	vocab_size=len(tokenizer.word_index) + 1

	# Select which embeddings to use
	if embedding_source == 'glove':
		# load pretrained glove embeddings
		glove_dict, embedding_matrix = load_glove_embeddings(tokenizer, vocab_size)
	elif embedding_source == 'fasttext':
		# Load in pretrained fasttext embeddings
		non_abusive_matrix, abusive_matrix, combined_matrix = load_fasttext_embeddings(tokenizer, vocab_size)
		list_embedding_matrix = [non_abusive_matrix, abusive_matrix, combined_matrix]


		if experiment_number == 1 or experiment_number == 3:
			# Non-abusive + Abusive embeddings
			embedding_matrix = list_embedding_matrix[2]
		elif experiment_number == 2:
			# Abusive
			embedding_matrix = list_embedding_matrix[1]

		

	print("############ Done converting text to embeddings #############", file=text_file)
	return embedding_matrix, tokenizer



def create_sequences(x, embedding_matrix, tokenizer):
	# Convert words to sequences
	x_seq = tokenizer.texts_to_sequences(x)

	# Filter empty messages
	filtered_list = []
	exclude_list = []
	counter = 0
	for i in x_seq:
		if len(i) < 1:
			exclude_list.append(counter)
		else:
			filtered_list.append(i)
		counter += 1


	x_list = np.array([sent_vectorizer(i, embedding_matrix) for i in filtered_list])

	return x_list, exclude_list



def filterEmptyMessages(y_set, exclude_list):
	filtered_y= []
	counter = 0
	for i in y_set:
		if counter not in exclude_list:
			filtered_y.append(i)
		counter += 1

	return filtered_y




"""
################# Main control of program
"""
def main(argv):
	# python3 modelSVM.py classification_type-exp_number-input_type-embeddings-distribution-batch_size-gold_data
	# python3 modelSVM.py multiclass-1-embeddings-fasttext-252550-24000-abuseval
	# python3 modelSVM.py multiclass-2-NA-NA-abuseval
	######### Determine settings of the experiment:
	arg = argv[1].strip('\n').split('-')


	# Main settings:
	classification_type = arg[0]
	experiment_number = int(arg[1])
	input_type = arg[2]
	cross_val = False


	if input_type == 'embeddings':
		embedding_source = arg[3]
	else:
		embedding_source = "NA"

	# Assign data sources and distributions to variables
	if experiment_number == 1:
		data_source = "reddit_distant" #gold_train #reddit+gold
		distribution = arg[4]
		batch_train_file = arg[5]
		gold_train_file = arg[6]
		model = 'svm-{}-{}-{}-{}-{}-{}-{}.joblib'.format(classification_type, experiment_number, input_type, embedding_source, data_source, str(distribution), str(batch_train_file))
		tokenizer_name = 'svm-{}-{}-{}-{}-{}-{}-{}.pickle'.format(classification_type, experiment_number, input_type, embedding_source, data_source, str(distribution), str(batch_train_file))
	elif experiment_number == 2:
		data_source = "gold_train"
		distribution = arg[4]
		batch_train_file = arg[5]
		gold_train_file = "../../data/training/gold_train/train_{}.csv".format(arg[6])
		model = 'svm-{}-{}-{}-{}-{}.joblib'.format(classification_type, experiment_number, input_type, embedding_source, arg[6])
		tokenizer_name = 'svm-{}-{}-{}-{}-{}.pickle'.format(classification_type, experiment_number, input_type, embedding_source, arg[6])
	elif experiment_number == 3:
		data_source = "reddit+gold"
		distribution = arg[4]
		batch_train_file = arg[5]
		gold_train_file = "../../data/training/gold_train/train_{}.csv".format(arg[6])
		model = 'svm-{}-{}-{}-{}-{}-{}-{}-{}.joblib'.format(classification_type, experiment_number, input_type, embedding_source, data_source, str(distribution), str(batch_train_file), arg[6])
		tokenizer_name = 'svm-{}-{}-{}-{}-{}-{}-{}-{}.pickle'.format(classification_type, experiment_number, input_type, embedding_source, data_source, str(distribution), str(batch_train_file), arg[6])


	# Write program details to outputfile
	global text_file 
	text_file = open("output/output_svm-{}-{}-{}-{}-{}-{}.txt".format(classification_type, experiment_number, input_type+embedding_source, distribution, batch_train_file, arg[6]), "a+")
	print("############ New model #############", file=text_file)
	print(arg, file=text_file)

	print("Classification_type: {}\n\
		Inputtype: {}\n\
		Experiment_number: {}\n\
		Data_source: {}\n\
		Distribution: {}\n\
		Batch_train_file: {}\n\
		Gold_train_file: {}\n\
		Embeddings_source: {}\n\
		".format(classification_type, input_type, experiment_number, data_source, distribution, batch_train_file, arg[6], embedding_source), file=text_file)

	



	# Load in training data
	combined_data = loadTrainingData(data_source, distribution, batch_train_file, gold_train_file, classification_type)
	x_train, y_train = combined_data['text'].astype(str).values, combined_data['labels'].values

	
	existing_models = []
	for (_, _, filenames) in walk('/data/s2769670/scriptie/models_saved/svm/exp{}/models/'.format(experiment_number)):
		existing_models.extend(filenames)
		break
	print(existing_models, model)
	#print(model, file=text_file)

	# Dictionary for storing the results from the testsets
	results_dict = {}

	if input_type == 'tfidf':
		if cross_val:
			input_dict = {}
			input_dict['distant252550'] = pd.read_csv("../../data/test/distant_testdata252550.csv", names=['id', 'text', 'distant_labels'], sep='\t', header = 0)
			input_dict['distant333333'] = pd.read_csv("../../data/test/distant_testdata333333.csv", names=['id', 'text', 'distant_labels'], sep='\t', header = 0)

			test_dict = {}
			for testset in input_dict.keys():
				X_test_distant = input_dict[testset]['text'].astype(str).values

				# Convert y labels
				if classification_type == 'binary':
					mapping_dict = {'0': 0, '1' : 1, '2' : 1, '0.0': 0, '1.0' : 1, '2.0' : 1, 'NOT': 0, 'IMP' : 1, 'EXP' : 1,}
				else:
					mapping_dict = {'0': 0, '1' : 1, '2' : 2, '0.0': 0, '1.0' : 1, '2.0' : 2, 'NOT': 0, 'IMP' : 1, 'EXP' : 2,}
				input_dict[testset]['converted_labels'] = input_dict[testset]['distant_labels'].apply(lambda x: mapping_dict[str(x)])
				y_test_distant = input_dict[testset]['converted_labels'].values
				test_dict[testset] = [X_test_distant, y_test_distant]
			test_scores = cross_validation(x_train, y_train, input_type, test_dict)
		else:
			# Check for existing models else train a new model
			if model in existing_models:
				text_clf = load('../models_saved/svm/exp{}/models/{}'.format(experiment_number, model))
				print("Loaded saved model", file=text_file)
			else:
				# Train classifier
				text_clf = train_model(x_train, y_train, input_type)

				# Save model
				# /data/s2769670/scriptie/
				dump(text_clf, '../models_saved/svm/exp{}/models/{}'.format(experiment_number, model))
		
			# Load all testdata
			test_dict = loadTestData(classification_type)

			# Evaluate model on test sets
			for testset in test_dict.keys():
				#print("\n### {} ###\n".format(testset))
				x_test, y_test = test_dict[testset].text.astype(str).values, test_dict[testset].labels.values
				results = evaluation(text_clf, x_test, y_test, classification_type, testset)

				# Add results to dictorary {'testset': result_dict}
				results_dict[testset] = results
	elif input_type == 'embeddings':
		# Create embeddings for trainingset
		embedding_matrix, tokenizer = create_embeddings(x_train, embedding_source, experiment_number, model, existing_models, tokenizer_name)

		# Convert trainingdata to sequences
		x_train, exclude_list = create_sequences(x_train, embedding_matrix, tokenizer)
		y_train = filterEmptyMessages(y_train, exclude_list)

		if cross_val:
			input_dict = {}
			input_dict['distant252550'] = pd.read_csv("../../data/test/distant_testdata252550.csv", names=['id', 'text', 'distant_labels'], sep='\t', header = 0)
			input_dict['distant333333'] = pd.read_csv("../../data/test/distant_testdata333333.csv", names=['id', 'text', 'distant_labels'], sep='\t', header = 0)

			test_dict = {}
			for testset in input_dict.keys():
				# Retrieve X labels
				X_test_distant, exclude_list = create_sequences(input_dict[testset]['text'].astype(str).values, embedding_matrix, tokenizer)

				# Convert y labels
				if classification_type == 'binary':
					mapping_dict = {'0': 0, '1' : 1, '2' : 1, '0.0': 0, '1.0' : 1, '2.0' : 1, 'NOT': 0, 'IMP' : 1, 'EXP' : 1,}
				else:
					mapping_dict = {'0': 0, '1' : 1, '2' : 2, '0.0': 0, '1.0' : 1, '2.0' : 2, 'NOT': 0, 'IMP' : 1, 'EXP' : 2,}
				input_dict[testset]['converted_labels'] = input_dict[testset]['distant_labels'].apply(lambda x: mapping_dict[str(x)])

				# convert y labels
				y_test_distant = filterEmptyMessages(input_dict[testset]['converted_labels'].values, exclude_list)	
				test_dict[testset] = [X_test_distant, y_test_distant]

			test_scores = cross_validation(x_train, y_train, input_type, test_dict)
		else:
			# Check for existing models else train a new model
			if model in existing_models:
				text_clf = load('../models_saved/svm/exp{}/models/{}'.format(experiment_number, model))
			else:
				# Train classifier
				text_clf = train_model(x_train, y_train, input_type)

				# Save model
				dump(text_clf, '../models_saved/svm/exp{}/models/{}'.format(experiment_number, model))
			
			# Load all testdata
			test_dict = loadTestData(classification_type)

			
			# Evaluate model on test sets
			for testset in test_dict.keys():
				#print("### {} ###".format(testset))
				x_test, y_test = test_dict[testset].astype(str).text.values, test_dict[testset].labels.values

				x_test, exclude_list = create_sequences(x_test, embedding_matrix, tokenizer)
				y_test = filterEmptyMessages(y_test, exclude_list)
				results = evaluation(text_clf, x_test, y_test, classification_type, testset)

				# Add results to dictorary {'testset': result_dict}
				results_dict[testset] = results

		
	if cross_val:
		# Write cross_val output to csv file
		# Open csv file for output program
		print("######## Writing output to csv ########", file=text_file)
		fields=['date', 'classification_type', 'input_type', 'embedding_source', 'train_distribution', 'batch_size','cross_val_accuracy', 'cross_val_macro-f1', 'distant252550_accuracy', 'distant252550_macro-f1', 'distant333333_accuracy', 'distant333333_macro-f1']
		csvfile = open('crossval_svm_results.csv', 'a+')
		writer = csv.DictWriter(csvfile, fieldnames = fields)    
		writer.writeheader()

		# Get time
		time = datetime.datetime.now()
		date_time = "{}-{}-{}_{}:{}".format(time.day, time.month, time.year, time.hour, time.minute)
		row = {"date": date_time,
					   "classification_type": classification_type,
					   "input_type": input_type,
					   "embedding_source": embedding_source,
					   "train_distribution": distribution,
					   "batch_size": batch_train_file,
				}
		# Add scores to row
		for testset in test_scores.keys():
			for scores in test_scores[testset].keys():
				row[testset + '_' + scores] = round(test_scores[testset][scores], 4)
			
		writer.writerow(row)

	else:
		# Write experiment settings and output to csvfile
		# Open csv file for output program
		print("######## Writing output to csv ########", file=text_file)
		fields=['date','experiment','classification_type', 'input_type', 
				'data_source', 'train_distribution', 'batch_size', 'gold_train_file', 'embedding_source', 'testdata', 'accuracy_score', 'macro-f1', 
				'label', 'precision', 'recall', 'f1-score', 'support']
		csvfile = open('results/exp{}_svm_results.csv'.format(experiment_number), 'a+')
		
		writer = csv.DictWriter(csvfile, fieldnames = fields)    
		writer.writeheader()

		# Add experiment settings to csv file
		for row_counter, testset in enumerate(results_dict.keys()):
			row = {}
			# Write first row
			if row_counter == 0:
				# Get time
				time = datetime.datetime.now()
				date_time = "{}-{}-{}_{}:{}".format(time.day, time.month, time.year, time.hour, time.minute)
				row = {"date": date_time,
					   "experiment": experiment_number,
					   "classification_type": classification_type,
					   "input_type": input_type,
					   "data_source": data_source,
					   "gold_train_file": arg[6],
					   'train_distribution': distribution,
					   "batch_size": batch_train_file,
					   "embedding_source": embedding_source
				}
				
			for item_counter, label in enumerate(results_dict[testset].keys()):
				#print(label)
				if item_counter == 0:
					row["testdata"] =  testset
					row["accuracy_score"] = round(results_dict[testset]['accuracy'], 4)
					row["macro-f1"] = round(results_dict[testset]['macro avg']['f1-score'], 4)
					row["label"] = "0"
					row["precision"] = round(results_dict[testset]["0"]['precision'], 4)
					row["recall"] = round(results_dict[testset]["0"]['recall'], 4)
					row["f1-score"] = round(results_dict[testset]["0"]['f1-score'], 4)
					row["support"] = results_dict[testset]["0"]['support']
					#writer.writerow(row)
				else:
					# Write other rows
					if label in ["1", "2", "macro avg", "weighted avg"]:
						row = {"label": label,
							   "precision": round(results_dict[testset][label]['precision'], 4),
							   "recall": round(results_dict[testset][label]['recall'], 4),
							   "f1-score": round(results_dict[testset][label]['f1-score'], 4),
							   "support": results_dict[testset][label]['support']
							   }
					else: 
						continue
				writer.writerow(row)

		writer.writerow({})

	csvfile.close()
	text_file.close()

if __name__ == '__main__':
	main(sys.argv)

