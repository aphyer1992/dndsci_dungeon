import itertools
import math
import random

random.seed('dungeon')

def roll_die(n):
    return(math.ceil(random.random() * n))


def roll_dice(n, d):
    mysum = 0
    for i in range(d):
        mysum += roll_die(n)
    return(mysum)

encounter_types = [
    {'short_name' : 'N', 'name' : 'Nothing', 'tier' : -1, 'asleep_damage' : 0, 'awake_damage' : 0, 'woken_by' : 0},
    {'short_name' : 'G', 'name' : 'Goblins', 'tier' : 1, 'asleep_damage' : 1, 'awake_damage' : 2, 'woken_by' : 0},
    {'short_name' : 'W', 'name' : 'Whirling Blade Trap', 'tier' : 1, 'asleep_damage' : 2, 'awake_damage' : 2, 'woken_by' : 0},
    {'short_name' : 'O', 'name' : 'Orcs', 'tier' : 2, 'asleep_damage' : 2, 'awake_damage' : 4, 'woken_by' : 1},
    {'short_name' : 'B', 'name' : 'Boulder Trap', 'tier' : 2, 'asleep_damage' : 3, 'awake_damage' : 3, 'woken_by' : 0},
    {'short_name' : 'C', 'name' : 'Clay Golem', 'tier' : 3, 'asleep_damage' : 4, 'awake_damage' : 4, 'woken_by' : 0},
    {'short_name' : 'H', 'name' : 'Hag', 'tier' : 3, 'asleep_damage' : 3, 'awake_damage' : 6, 'woken_by' : 2},
    {'short_name' : 'S', 'name' : 'Steel Golem', 'tier' : 4, 'asleep_damage' : 5, 'awake_damage' : 5, 'woken_by' : 0},
    {'short_name' : 'D', 'name' : 'Dragon', 'tier' : 4, 'asleep_damage' : 4, 'awake_damage' : 8, 'woken_by' : 3},
]

encounter_dict = {}
for e in encounter_types:
    encounter_dict[e['short_name']] = e

class Dungeon:
    def __init__(self, encounters, verbose=False):
        self.encounters = [
            [encounters[0], encounters[1], encounters[2]],
            [encounters[3], encounters[4], encounters[5]],
            [encounters[6], encounters[7], encounters[8]],
        ]
        self.encounters_awake = [
            [False, False, False],
            [False, False, False],
            [False, False, False],
        ]
        self.nondeterministic = False
        self.ambiguities = {}
        if verbose:
            print('Set up a dungeon:\n')
            self.print()

    def has_unresolved_ambiguity(self):
        for a in self.ambiguities.keys():
            if len(self.ambiguities[a]) < 2:
                return True
        return False

    def reset_sleep(self):
        self.encounters_awake = [
            [False, False, False],
            [False, False, False],
            [False, False, False],
        ]

    def print(self):
        for r in self.encounters:
            print(r)

    def encounter_difficulty(self, loc):
        e = self.encounters[loc[0]][loc[1]]
        awake_key = 'awake_damage' if self.encounters_awake[loc[0]][loc[1]] else 'asleep_damage'

        return(encounter_dict[e][awake_key])

    def calculate_score(self, verbose=False):
        score = 0
        chain = []
        loc = (0,0)

        while True:
            score = score + self.encounter_difficulty(loc)
            chain.append('{}:{}'.format(self.encounters[loc[0]][loc[1]], self.encounter_difficulty(loc)))

            # figure out which squares are legal moves
            options = []
            if loc[0] < 2:
                options.append((loc[0] + 1, loc[1]))
            if loc[1] < 2:
                options.append((loc[0], loc[1] + 1))
            # if we have just resolved 2,2 we can break
            if len(options) == 0:
                break

            # any encounter at one of those legal moves may wake up
            current_tier = encounter_dict[self.encounters[loc[0]][loc[1]]]['tier']
            for o in options:
                e = self.encounters[o[0]][o[1]]
                if encounter_dict[e]['woken_by'] <= current_tier:
                    self.encounters_awake[o[0]][o[1]] = True

            # if multiple legal moves, adventurers scout for who seems easiest.
            best_options = []
            best_score = None

            for o in options:
                option_score = self.encounter_difficulty(o)
                if best_score is None or best_score > option_score:
                    best_score = option_score
                    best_options = []
                if best_score == option_score:
                    best_options.append(o)

            if len(best_options) > 1:
                self.nondeterministic = True
                if o not in self.ambiguities.keys():
                    self.ambiguities[o] = []
                visited_options = self.ambiguities[o]
                unvisited_best_options = [b for b in best_options if b not in visited_options]
                if len(unvisited_best_options):
                    loc = random.choice(unvisited_best_options)
                else: # we could hit this if there was another ambiguity later
                    loc = random.choice(best_options)
                # mark as visited for later.
                if loc not in self.ambiguities[o]:
                    self.ambiguities[o].append(loc)
            else:
                loc = random.choice(best_options)

        if verbose:
            print('Scored {} via chain:'.format(score))
            print(chain)

        return((score, chain))

def evaluate_dungeon(i, long=False):
    d = Dungeon(list(i[0:9]))
    dungeon_runs = 1
    dungeon_scores = [d.calculate_score()]
    while d.has_unresolved_ambiguity():
        dungeon_runs += 1
        assert(dungeon_runs < 1e3)
        d.reset_sleep()
        new_score = d.calculate_score()
        if new_score not in dungeon_scores: # this also includes the path taken
            dungeon_scores.append(new_score)

    numerical_scores = [d[0] for d in dungeon_scores]

    data = {
        'details' : dungeon_scores,
        'encounters': i,
        'num_paths' : len(numerical_scores),
        'avg_score' : sum(numerical_scores) / len(numerical_scores),
        'min_score' : min(numerical_scores),
        'max_score' : max(numerical_scores),
    }

    if long:
        data['scores'] = dungeon_scores

    return(data)

def evaluate_encounter_list(encounter_list):
    scores = []

    permutations = list(itertools.permutations(encounter_list))
    permutations = list(set(permutations)) # uniq-ify
    runs = 0
    for i in permutations:
        runs += 1
        data = evaluate_dungeon(i)
        scores.append(data)
        #if runs%5e4 == 0:
            #print(runs)


    scores.sort(key=lambda x: x['min_score'])

    return(scores)

def buy_random_encounter():
    while True:
        e = random.choice(encounter_types)
        if e['name'] == 'Nothing':
            continue
        if random.random() * 5 < e['tier']:
            continue
        return(e['short_name'])

def order_encounters(encounter_list):
    while len(encounter_list) > 9:
        remove_tier = min([encounter_dict[e]['tier'] for e in encounter_list])
        remove_options = [e for e in encounter_list if encounter_dict[e]['tier'] == remove_tier]
        encounter_list.remove(random.choice(remove_options))

    while len(encounter_list) < 9:
        encounter_list.append('N')

    random.shuffle(encounter_list)
    treasure_guard_options = [encounter_list[0], encounter_list[1], encounter_list[2]]
    treasure_guard_tier = max([encounter_dict[e]['tier'] for e in treasure_guard_options])
    treasure_guard_options = [e for e in treasure_guard_options if encounter_dict[e]['tier'] == treasure_guard_tier]
    treasure_guard = treasure_guard_options[0]
    encounter_list.remove(treasure_guard)
    random.shuffle(encounter_list)
    encounter_list.append(treasure_guard)
    return(encounter_list)

def gen_dragon_princess_encounters(round_no):
    encounters = ['D']
    if round_no > 3286 and round_no < 9816:
        encounters.append('D')

    num_random = 5 + roll_die(6)
    for i in range(num_random):
        encounters.append(buy_random_encounter())

    return encounters

def gen_orc_chief_encounters(round_no):
    encounters = ['G', 'G', 'G', 'G', 'G', 'O']
    if round_no > 9816:
        encounters.append('O')
        encounters.append('O')

    num_random = 2 + roll_die(6)
    for i in range(num_random):
        encounters.append(buy_random_encounter())

    return encounters

def gen_trapmaster_encounters(round_no):
    encounters = []
    for i in range(4):
        encounters.append(random.choice(['B', 'W']))

    num_random = 2 + roll_die(6)
    for i in range(num_random):
        encounters.append(buy_random_encounter())

    return encounters

def gen_golemancer_encounters(round_no):
    encounters = ['C']
    num_random = 5 + roll_die(6)

    if round_no > 944:
        num_random -= 1
        encounters.append('S')

    if round_no > 3122:
        num_random -= 1
        encounters.append('C')

    for i in range(num_random):
        encounters.append(buy_random_encounter())

    return encounters

def gen_random_entrant_encounters(round_no):
    encounters = []
    num_random = 4 + roll_die(6) + roll_die(4)
    for i in range(num_random):
        encounters.append(buy_random_encounter())

    return encounters

def write_log_row(log_row, mode='a'):
        log_string = ','.join([str(e) for e in log_row])+"\n"
        f = open('dungeon_output.csv', mode)
        f.write(log_string)

def setup_logs():
    row = ['Tournament #', 'Dungeon Owner']
    for i in range(1,10):
        row.append('Encounter {}'.format(i))
    row.append('Average Score')
    for i in range(1,5):
        row.append('Score {}'.format(i))
    write_log_row(row, mode='w')

def run_tournament(round_no):
    contestants = [
        gen_dragon_princess_encounters(round_no),
        gen_orc_chief_encounters(round_no),
        gen_trapmaster_encounters(round_no),
        gen_golemancer_encounters(round_no)
    ]
    num_random = roll_die(4) - 1
    if random.random() * 1e4 > round_no:
        num_random += 1
    for i in range(num_random):
        contestants.append(gen_random_entrant_encounters(round_no))

    contestants = [order_encounters(c) for c in contestants]

    accepted = False
    while not accepted:
        num_judges = roll_die(4) + 1
        accepted = True
        if num_judges == 5 and random.random() < round_no * 2126:
            accepted = False
        if num_judges == 2 and random.random() < (7126 - round_no) * 1448:
            accepted = False

    random.shuffle(contestants)

    for c in contestants:
        log_row = [round_no, contestants.index(c)]
        for i in c:
            log_row.append(encounter_dict[i]['name'])
        d = Dungeon(list(c[0:9]))
        scores = []
        details = []
        for i in range(num_judges):
            d.reset_sleep()
            res = d.calculate_score()
            score = roll_dice(2, res[0])
            scores.append(score)
            details.append('{} ({}d, {})'.format(score, res[0], '-'.join(res[1])))
        average_score = sum(scores) / len(scores)
        log_row.append(average_score)
        log_row = log_row + details
        write_log_row(log_row)
        
#setup_logs()
#for i in range(1,9861):
#    run_tournament(i)

#player = evaluate_encounter_list(['G', 'G', 'W', 'O', 'O', 'B', 'H', 'C', 'D'])
#player2 = evaluate_encounter_list(['N', 'N', 'W', 'O', 'O', 'B', 'H', 'C', 'D'])
#scores = evaluate_encounter_list(player)
#scores2 = evaluate_encounter_list(player2)
#assert(False)

#encounters = ['M', 'G', 'W', 'P', 'B', 'G', 'O', 'H', 'D']
#for i in range(5):
#    d = Dungeon(encounters, verbose=True)
#    score = d.calculate_score(verbose=True)
#assert(False)

encounter_lists = []

for e in encounter_dict.keys():
    base_list = list(encounter_dict.keys())
    base_list.remove(e)
    for e2 in encounter_dict.keys():
        for e3 in encounter_dict.keys():
            if e in [e2, e3]:
                continue
            if e2 > e3:
                continue
            encounter_lists.append(base_list + [e2, e3])

print('Have {} lists to try out...'.format(len(encounter_lists)))

summary_data = []
encounter_lists = [['G', 'G', 'W', 'O', 'O', 'B', 'H', 'C', 'D'], ['N', 'N', 'W', 'O', 'O', 'B', 'H', 'C', 'D']]

for encounter_list in encounter_lists:
    print('Trying with:')
    print(encounter_list)
    scores = evaluate_encounter_list(encounter_list)
    best_score = scores[-1]['min_score']
    num_best = 1
    while scores[-1 * num_best]['min_score'] == best_score:
        num_best += 1
    average_min_score = sum([s['min_score'] for s in scores])/len(scores)
    print('Best minimum score is {}, available in {} ways'.format(best_score, num_best, average_min_score))

    scores.sort(key=lambda x: x['avg_score'])

    best_score = scores[-1]['avg_score']
    num_best = 1
    while scores[-1 * num_best]['avg_score'] == best_score:
        num_best += 1
    average_avg_score = sum([s['avg_score'] for s in scores])/len(scores)
    print('Best average score is {}, available in {} ways.  Average is {}'.format(best_score, num_best, average_avg_score))




    summary_data.append({
        'encounters': encounter_list,
        'num_best' : num_best,
        'best_score' : best_score,
        'average_score' : average_avg_score,
    })
