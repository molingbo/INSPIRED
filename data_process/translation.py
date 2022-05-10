import json
import re

# load mini_template_corpus
mini_template_corpus = json.load(open('./corpus/mini_template_corpus.json'))
# load multi_restriction_corpus
multi_restriction_corpus = json.load(open('./corpus/multi_restriction_corpus.json'))
# load template corpus
corpus = json.load(open('./corpus/template_corpus.json'))


def isDigit(x):
	try:
		if '-' in x: # '1997-06-12'
			return True 
		else:
			x = int(x) # '1997'
			return isinstance(x, int)
	except ValueError:
		return False

def get_sketch_triple(ori_input, template_corpus):

	ori_input = ori_input.replace('<sparql-header-1> ', '').replace('<sparql-header-2> ', '')

	if 'filter' in ori_input:

		filter_str = re.findall('(filter.*)\?x', ori_input)
		if filter_str != []:

			ori_input = ori_input.replace(filter_str[0], '')

	input = ori_input.split(' . ')
	input[-1] = input[-1][:-2]

	bridge_mark = False
	c_count = 0
	for item in input:
		if '?c' in item:
			c_count+=1
	if c_count >= 2 and '?c . ?c' not in ori_input:
		bridge_mark = True

	result = {}
	count = 0
	for i in range(len(input)):
		if input[i].startswith('filter'):
			break
		if i == 0:
			count += 1
			result[count] = [input[i]]
		else:	

			if input[i][0:2] == input[i-1][-2:] and input[i][0:2] != '?x' and 'time.event' not in input[i]:
				if input[i].startswith('?'):
					if len(result[count]) == 1:
						result[count].append(input[i])
					else:
						count += 1
						result[count] = [input[i]]

			else:
				if input[i].startswith('?'):
					count += 1
					result[count] = [input[i]]		

	concat_result = []
	for key in result:
		concat_result.append( ' '.join(result[key]) )

	sketch = []
	for item in result:
		if len(result[item]) == 1:

			temp = result[item][0].split()

			temp[1] = [ temp[1].replace('ns:', '') ]

			sketch.append(temp)
		else:
			temp = []
			temp1 = result[item][0].split()[0:-1]
			temp2 = result[item][1].split()[1:]
			temp.append(temp1[0])
			predicates = []
			predicates.append(temp1[1].replace('ns:', ''))
			predicates.append(temp2[0].replace('ns:', ''))
			temp.append(predicates)
			temp.append(temp2[1])
			sketch.append(temp)

	num_x = 0
	for item in concat_result:
		if '?x' in item:
			num_x += 1


	compile_sketch = []
	# One scenario (constraint triple with ?x)
	if num_x >= 3 or (num_x==2 and bridge_mark):

		notable_type_mark = False # recognize common.topic.notable_types occured at the beginning
		for i, ske in enumerate(sketch):
			if i == 0 and ske[1][0] == 'common.topic.notable_types':
				notable_type_mark = True
				continue

			if str(ske[1]) not in template_corpus and not ske[1][0].startswith('Of these') or ske[1][0] == 'common.topic.notable_types':
				try:
					compile_sketch[-1].append(ske)
				except IndexError:
					continue
			else:
				compile_sketch.append([ske])

		if notable_type_mark:
			compile_sketch[0].append(sketch[0])

	# The other scenario (constraint triple without ?x)
	else:

		for i, (concat, ske) in enumerate(zip(concat_result, sketch)):
			if '?x' not in concat  and '?c' not in concat:
				head_var = concat[0:2]+' '

				for j, concat_ in enumerate(concat_result):

					if head_var in concat_:
						try:
							compile_sketch[j].append(ske)
							break
						except IndexError:
							continue
						
			else:

				compile_sketch.append([ske])
		if len(sketch) > len(concat_result):
			compile_sketch.append([sketch[-1]])

	return compile_sketch

def translate(lf):

	input = lf.replace('<sparql-header-1> ', '').replace('<sparql-header-2> ', '')

	r_type = '' # reasoning type
	if '?c' in input and '?c . ?c' not in input:
		r_type = 'bridging'
	else:
		r_type = 'intersection'

	order_by = '' # order by, order by desc
	date_time = False # order by + datetime, order by desc + datetime
	num = False # order by ( ?num ), order by desc ( ?num ) 
	integer_num = False # order by xsd:integer ( ?num ), order by desc ( xsd:integer ( ?num )
	if 'order by desc' in input:
		order_by = 'decrease'
		if 'order by desc ( xsd:datetime' in input:
			date_time = True
		if 'order by desc ( xsd:integer ( ?num )' in input:
			integer_num = True
		if 'order by desc ( ?num )' in input:
			num = True
	elif 'order by' in input:
		order_by = 'increase'
		if 'order by xsd:datetime' in input:
			date_time = True
		if 'order by xsd:integer ( ?num )' in input:
			integer_num = True
		if 'order by ?num' in input:
			num = True
	else:
		order_by = ''

	before_after = ''
	if 'filter ( ?num >' in input:
		before_after = ' after '
	elif 'filter ( ?num <' in input:
		before_after = ' before '
	else:
		before_after = ' in '

	# Consider the "filter"
	middle_datetime = ''
	last_datetime = ''
	if 'filter' in input:

		filter_str = re.findall('(filter.*)\?x', input) # filter, exist ...
		if filter_str != []:
			date_str = re.findall('\'\' (.*?) \`\`', filter_str[0])

			if date_str != []:
				middle_datetime = date_str[0].split('-')[0]

			input = input.replace(filter_str[0], '')

		if 'filter' in input:
			filter_str = re.findall('(filter.*)', input)
			date_str = re.findall('\'\' (.*?) \`\`', filter_str[0])
			if 'not exists' in filter_str[0]:

				if date_str != []:
					last_datetime = date_str[0].split('-')[0]
			else:
				if date_str != []:
					last_datetime = date_str[0]
		else:
			date_str = re.findall('\'\' (.*) \`\`', input)
			if date_str != []:
				last_datetime = date_str[0]

	sketch = get_sketch_triple(input, corpus)

	translated_questions = []

	for index, j in enumerate(sketch):

		template = list(corpus.values())[list(corpus.keys()).index(str(j[0][1]))]
		temp = template[0]

		# handle restriction issue
		if len(j) > 1:
			mini_template = mini_template_corpus[j[1][1][0]]
			mini_template = mini_template.replace('<MINI_PLD>', j[1][2])
			if '<RSTR>' in temp:
				if str(j[0][1]) in multi_restriction_corpus:
					if j[1][1][0] in multi_restriction_corpus[str(j[0][1])]:
						temp = temp.replace('<RSTR>', mini_template)
				else:
					temp = temp.replace(' <RSTR>', '')
					temp = temp + ' ' + mini_template
			else:
				temp = temp + ' ' + mini_template

		temp = temp.replace(' <RSTR>', '') # if there's no matched restriction predicate

		h_index = 0 # head index
		t_index = 2 # tail index

		if isDigit(j[0][2]): # deal with: miss ?num
			temp = temp.replace('<PLD>', j[0][2])

		if j[0][h_index].startswith('#') or j[0][h_index] == '?num':
			temp = j[0][h_index] + ' is/are ' + temp
		elif j[0][h_index] == '?x':
			if r_type == 'bridging' or (r_type == 'intersection' and index == 0):
				temp = 'What is/are ' + temp
			else:
				temp = 'Of which, what is/are ' + temp
		elif j[0][h_index] == '?c' and r_type == 'bridging':
			if index == 0:
				temp = 'What is/are ' + temp
			else: 
				temp = '<ANS> is/are ' + temp	


		if j[0][t_index].startswith('#') or j[0][t_index] == '?num':
			temp = temp.replace('<PLD>', j[0][t_index])
		elif j[0][t_index] == '?x':
			if r_type == 'bridging' or (r_type == 'intersection' and index == 0):
				temp = temp.replace('<PLD>', 'what') if '<PLD>' in temp else 'What is/are ' + temp
			else:
				temp = 'Of which, ' + temp.replace('<PLD>', 'what') if '<PLD>' in temp else 'Of which, what is/are ' + temp
		elif j[0][t_index] == '?c' and r_type == 'bridging':
			if index == 0:
				if '<PLD>' in temp:
					temp = temp.replace('<PLD>', 'what')
				else:
					if 'What is/are' not in temp:
				 		temp = 'What is/are ' + temp
			else:
				if '<PLD>' in temp:
					temp = temp.replace('<PLD>', '<ANS>')
				else:
					if 'What is/are' not in temp: 
						temp = 'What is/are ' + temp

		# consider filter
		if middle_datetime != '' and last_datetime == '' and index == len(sketch)-2:
			temp = temp + ' in ' + middle_datetime
		elif middle_datetime == '' and last_datetime != '' and index == len(sketch)-1:
			if '?num' in temp or '<PLD>' in temp:
				temp = temp.replace('?num', before_after[1:] +last_datetime).replace('<PLD>', before_after[1:] +last_datetime)
			else:
				temp = temp + ' in ' + last_datetime
		elif middle_datetime != '' and last_datetime != '':
			if index == len(sketch) - 2:
				temp = temp + ' in ' + middle_datetime
			elif index == len(sketch) - 1:
				if '?num' in temp or '<PLD>' in temp:
					temp = temp.replace('?num', before_after[1:] +last_datetime).replace('<PLD>', before_after[1:] +last_datetime)
				else:
					temp = temp + ' in ' + last_datetime

		translated_questions.append(temp)

	if order_by != '': # consider order_by
		if order_by == 'increase' and date_time:
			temp = 'Of these, which is the earliest'
		elif order_by == 'increase' and num:
			temp = 'Of these, which is the entity associated with the earliest date'
		elif order_by == 'increase' and integer_num:
			temp = 'Of these, which is the entity that has the least'
		elif order_by == 'increase':
			temp = 'Of these, which is the smallest'
		elif order_by == 'decrease' and date_time:
			temp = 'Of these, which is the latest'
		elif order_by == 'decrease' and num:
			temp = 'Of these, which is the entity associated with the latest date'
		elif order_by == 'decrease' and integer_num:
			temp = 'Of these, which is the entity that has the most'
		elif order_by == 'decrease':
			temp = 'Of these, which is the largest'
		translated_questions.append(temp)

	# post processing for remaining <PLD>, and superlative questions
	processed_trans_ques = []
	for j, item in enumerate(translated_questions):
		new_item = item.replace(' (?sk0)', '')
		if '<PLD>' in item:

			tmp = re.findall('\'\' (.*?)"', lf)
			if len(tmp) > 0:
				new_item = item.replace('<PLD>', tmp[0])

		if j == 1 and 'order by' != '':
			new_item = item.replace('Of which, what is/are', 'These entities are').replace('?num', 'what').replace('?sk0', 'what')

		# handle before_after issue
		preposition_words = ['on', 'from', 'since', 'until', 'in']
		for word in preposition_words:
			if word + ' before' in new_item:
				new_item = new_item.replace(word+' before', 'before')
			elif word + ' after' in new_item:
				new_item = new_item.replace(word+' after', 'after')

		new_item = new_item.replace(' in in ', ' in ')
		processed_trans_ques.append(new_item)

	return processed_trans_ques


if __name__ == "__main__":

	# Test translation functionality: 
	# input: preprocessed lf; output: translated sub-questions
	lf = "<sparql-header-1> ?c ns:organization.organization.leadership ?k . ?k ns:organization.leadership.person #entity1# . ?c ns:education.educational_institution.mascot ?x ."
	questions = translate(lf)
