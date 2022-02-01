from typing import Callable
import random

all_words = [w.strip().lower() for w in open('allow_words.txt', 'r').readlines()]

def _score_word(word, greens, yellows, blacks) -> int:
	score = 0
	for c in word:
		if c in greens:
			score += 2
		elif c in yellows:
			score += 5
		elif c in blacks:
			score += 1
		else:
			score += 10
		
	return score

def _get_best_guess(greens: dict, yellows: dict, blacks: dict, letter_counts: dict, letter_count: int) -> str:
	filters = _create_filters(greens, yellows, blacks, letter_counts)
	words = list(set([w.lower() for w in all_words if len(w) == letter_count and w.isalpha()]))
	random.shuffle(words)

	possible_words = list(_filter_words(filters, words))
	possible_words_set = set(possible_words)

	best_guess_words = [w for w in words if not w in possible_words_set]
	best_guess_words.sort(key=lambda x: _score_word(x, greens, yellows, blacks))
	bests__ = best_guess_words[-5:]
	print('Best ' + str(len(bests__)) + ' impossible words for guessing: ' + str(bests__))

	random.shuffle(possible_words)
	possible_words = possible_words[:70]
	print('Number of possible words count given knowledge: ', len(possible_words))

	guesses = []
	if len(possible_words) <= 3:
		guesses = list(possible_words)
	else:
		guesses = list(possible_words) + best_guess_words[-len(possible_words):]
	
	random.shuffle(guesses)
	guess_count = int(5000 / len(possible_words))
	guesses = guesses[:guess_count]

	print('Total guesses: ' + str(len(guesses)))

	best_word = guesses[0]
	best_word_count = len(words) + 1

	total_work = len(possible_words) * len(guesses)
	work_done = 0
	print('Total Comparisons: ' + str(total_work))

	for i in range(len(possible_words)):
		possible_winner = possible_words[i]
		for j in range(len(guesses)):
			possible_best_word = guesses[j]
			# If you can't win, next best thing is getting as close as possible
			if possible_winner == possible_best_word:
				continue

			new_filters = _create_filters_best_guess(possible_winner, possible_best_word, greens, yellows, blacks, letter_counts)
			new_possible_words_count = len(_filter_words(new_filters, words))
			work_done += 1
			if best_word_count < new_possible_words_count:
				continue
		
			best_word_count = new_possible_words_count
			best_word = possible_best_word
	
	return best_word

def _get_color(winner, guess):
	assert(len(winner) == len(guess))

	color = 'b' * len(winner)
	letters_left = winner
	for i in range(len(winner)):
		if winner[i] != guess[i]:
			continue
		color = _replacer(color, 'g', i)
		letters_left = letters_left.replace(winner[i], '', 1)
	
	for i in range(len(winner)):
		if not guess[i] in letters_left:
			continue
		color = _replacer(color, 'y', i)
		letters_left = letters_left.replace(guess[i], '', 1)
	
	return color

def _create_filters_best_guess(winner, guess, greens, yellows, blacks, letter_counts):
	color = _get_color(winner, guess)

	local_greens, local_yellows, local_blacks = _get_local_colors(guess, color)
	new_letter_counts = dict(letter_counts)

	new_greens = _merge_colors(greens, local_greens)
	new_yellows = _merge_colors(yellows, local_yellows)
	new_blacks = _merge_colors(blacks, local_blacks)

	for b in local_blacks.keys():
		new_letter_counts[b] = len(local_greens.get(b, [])) + len(local_yellows.get(b, []))
	
	return _create_filters(new_greens, new_yellows, new_blacks, new_letter_counts)


def _filter_words(filters: list, words: list[str]) -> list[str]:
	def is_possible_word(word):
		for f in filters:
			if f(word):
				continue
			return False
		return True

	return [w for w in words if is_possible_word(w)]

def _create_filters(greens: dict, yellows: dict, blacks: dict, letter_counts: dict) -> list:
	filters = []
	for g, indices in greens.items():
		for i in indices:
			filters.append(_create_must_include_with_index_lambda(g, i))
	
	for y, indices in yellows.items():
		for i in indices:
			filters.append(_create_must_include_lambda(y, i))
	
	for b, indices in blacks.items():
		if b in greens or b in yellows:
			continue 

		for i in indices:
			filters.append(_create_must_not_include_lambda(b))
	
	for letter, count in letter_counts.items():
		filters.append(_create_prevent_duplicate_lambda(letter, count))
	
	return filters

def _replacer(s, newstring, index, nofail=False):
    # raise an error if index is outside of the string
    if not nofail and index not in range(len(s)):
        raise ValueError("index outside given string")

    # if not erroring, but the index is still not in the correct range..
    if index < 0:  # add it to the beginning
        return newstring + s
    if index > len(s):  # add it to the end
        return s + newstring

    # insert the new string between "slices" of the original
    return s[:index] + newstring + s[index + 1:]

def _parse_knowledge_and_guess(guesses: list[str], colors: list[str], letter_count: int) -> str:
	greens = {}
	yellows = {}
	blacks = {}
	letter_counts = {}
	for i in range(len(guesses)):
		guess = guesses[i]
		color = colors[i]

		local_greens, local_yellows, local_blacks = _get_local_colors(guess, color)

		greens = _merge_colors(greens, local_greens)
		yellows = _merge_colors(yellows, local_yellows)
		blacks = _merge_colors(blacks, local_blacks)

		for b in local_blacks.keys():
			letter_counts[b] = len(local_greens.get(b, [])) + len(local_yellows.get(b, []))
	
	return _get_best_guess(greens, yellows, blacks, letter_counts, letter_count)

def _get_local_colors(guess: str, color: str):
	greens = {}
	yellows = {}
	blacks = {}

	for i in range(len(guess)):
		if color[i] == 'g':
			indices = greens.get(guess[i], [])
			indices.append(i)
			greens[guess[i]] = indices
		elif color[i] == 'y':
			indices = yellows.get(guess[i], [])
			indices.append(i)
			yellows[guess[i]] = indices
		elif color[i] == 'b':
			indices = blacks.get(guess[i], [])
			indices.append(i)
			blacks[guess[i]] = indices

	return greens, yellows, blacks

def _merge_colors(original: dict, other: dict) -> dict:
	new = dict(original)
	for color, indices in other.items():
		new_indices = new.get(color, []) + indices
		new[color] = new_indices
	return new

def _create_must_include_lambda(letter: str, index_found: int) -> Callable[[str], bool]:
	return lambda word: word[index_found] != letter and letter in word

def _create_must_include_with_index_lambda(letter: str, index: int) -> Callable[[str], bool]:
	return lambda word: word[index] == letter

def _create_must_not_include_lambda(letter: str) -> Callable[[str], bool]:
	return _create_prevent_duplicate_lambda(letter, 0)

def _create_prevent_duplicate_lambda(letter: str, amount: int) -> Callable[[str], bool]:
	return lambda word: word.count(letter) == amount

def _print_commands():
	print('Commands:')
	print('suggest\t\t- provides a suggestion word given the knowledge')
	print('reset\t\t- resets the knowledge')
	print('learn\t\t- allows you to enter knowledge')
	print('help\t\t- shows these sets of command')
	print('q or quit\t- stops the application')
	print()

def main():
	guesses = []
	colors = []

	_print_commands()

	while True:
		command = input('command >> ').strip().lower()
		print()

		if command == 'suggest':
			suggestion = _parse_knowledge_and_guess(guesses, colors, 5)
			print()
			print('Try: ' + suggestion)
			print()
			continue
		
		if command == 'reset':
			guesses = []
			colors = []
			print('Reset.')
			print()
			continue
		
		if command == 'q' or command == 'quit':
			print('Quitting...')
			print()
			break
		
		if command == 'learn':
			guess = input('Word: ').strip().lower()
			color = input('Colors: ').strip().lower()
			if len(guess) != len(color) and len(guess) != 5:
				print('Invalid input.')
				print()
				continue
			
			guesses.append(guess)
			colors.append(color)
			print('Catalogued knowledge.')
			print()
			continue
		
		if command == 'help':
			_print_commands()
			continue
		
		print('Invalid command. Use "help" to see commands.')

main()