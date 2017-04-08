# Author: TommyX
#
# Counterfeit coin riddle: https://www.youtube.com/watch?v=tE2dZLDJSjA
# This code uses genetic algorithm to solve the riddle by evolving strategies.
#
# Usage:
# - Run the script and wait until a solution is found (may take 20 - 300 generations).
# - The solution name each coin from 0 to 11, and instructs you on how to weight the coins.
# 
# TODO: Check if exhaustive search with recursion is faster than genetic algorithm

import random
import math


def random_chance(chance):
    return random.random() < chance

def random_select(array):
    return array[random.randint(0, len(array) - 1)]

def random_select_chance(chance_array):
    if len(chance_array) == 0:
        return -1

    options = len(chance_array) - 1
    pointer = 0
    total = 0.0
    for i in chance_array:
        total += i
   
    rand = random.random() * total
    while pointer < options - 1:
        chance = chance_array[pointer]
        if rand < chance:
            break
  
        rand -= chance
        total -= chance
        pointer += 1
 
    return pointer

def reorder_array(array, new_indices):
    result = [None for i in range(len(array))]
    for i in range(len(new_indices)):
        result[new_indices[i]] = array[i]
    
    return result

class Config:
    
    def __init__(self, fake_coin, fake_coin_heavy):
        self.fake_coin = fake_coin # indicates which coin is fake
        self.fake_coin_heavy = fake_coin_heavy # if true, then fake coin is heavier

    """
    returns which side is heavier, 0 if equal
    """
    def use_scale(self, selection):
        num_1 = 0
        num_2 = 0
        
        for i in selection.data:
            if i == 1: num_1 += 1
            elif i == 2: num_2 += 1
        
        if num_1 > num_2: return 1
        if num_2 > num_1: return 2

        result = selection.get(self.fake_coin)
        if (result == 0):
            return 0
        
        return result if self.fake_coin_heavy else (3 - result)
    
    def generate_all(coins):
        result = []
        for i in range(coins):
            result.append(Config(i, False))
            result.append(Config(i, True))
        
        return result
    
    def generate_random(coins):
        i = random.randint(0, coins - 1)
        return Config(i, True if random_chance(0.5) else False)
            
class Selection:
    MAX_BITS = 12
    
    def __init__(self, data):
        self.data = data;
        for i in range(len(data), Selection.MAX_BITS):
            self.data.append(0)
    
    def set(self, i, val):
        self.data[i] = val
        
    def get(self, i):
        return self.data[i]
    
    def __str__(self):
        left_indices  = []
        right_indices = []
        for i in range(len(self.data)):
            if self.data[i] == 1:
                left_indices.append(i)
                
            elif self.data[i] == 2:
                right_indices.append(i)
            
        return "Compare " + str(left_indices) + " and " + str(right_indices)
    
    def duplicate(self):
        return Selection(self.data[:])
    
    def polish(self, ordering, known_equal):
        self.data = reorder_array(self.data, ordering)
        
        left_indices_equal  = []
        right_indices_equal = []
        for i in range(len(self.data)):
            if i not in known_equal:
                continue
            
            if self.data[i] == 1:
                left_indices_equal.append(i)
                
            elif self.data[i] == 2:
                right_indices_equal.append(i)
        
        for i in range(min(len(left_indices_equal), len(right_indices_equal))):
            self.data[left_indices_equal[i]]  = 0
            self.data[right_indices_equal[i]] = 0
    
    def mutate(self, chance, coins):
        # mutating
        for i in range(coins):
            if (random_chance(chance)):
                self.data[i] = random.randint(0, 2)
        
        # balancing
        num = [0, 0, 0]
        
        for i in range(coins):
            if self.data[i] == 1: num[1] += 1
            elif self.data[i] == 2: num[2] += 1
        
        greater = 0
        if num[1] > num[2]: greater = 1
        if num[2] > num[1]: greater = 2
        
        if greater != 0:
            fewer = 3 - greater
            target = num[1] + num[2]
            if target & 1:
                if random_chance(0.5):
                    target = target // 2
                
                else:
                    target = (target // 2) + 1
                
            else:
                target //= 2
            
            # remove the greater ones
            greater_i = []
            for i in range(coins):
                if self.data[i] == greater:
                    greater_i.append(i)
            
            random.shuffle(greater_i)
            
            for i in range(num[greater] - target):
                self.data[greater_i[i]] = 0
            
            # add the fewer ones
            zero_i = []
            for i in range(coins):
                if self.data[i] == 0:
                    zero_i.append(i)
            
            random.shuffle(zero_i)
            
            for i in range(target - num[fewer]):
                self.data[zero_i[i]] = fewer
    
    def generate_random(num_1, num_2, coins):
        data = []
        for i in range(num_1):
            data.append(1)
            
        for i in range(num_2):
            data.append(2)
        
        for i in range(coins - num_1 - num_2):
            data.append(0)
        
        random.shuffle(data)
        
        return Selection(data)
    
    def generate_all(num_1, num_2, coins):
        if ((coins == 0) or (num_1 == 0 and num_2 == 0)):
            return [Selection([])]
        
        result = []
        for i in range(num_1 + num_2 - 1, coins):
            if (num_1 > 0): 
                sub_result = Selection.generate_all(num_1 - 1, num_2, i)
                for item in sub_result:
                    item.set(i, 1)
                    result.append(item)
                
            if (num_2 > 0): 
                sub_result = Selection.generate_all(num_1, num_2 - 1, i)
                for item in sub_result:
                    item.set(i, 2)
                    result.append(item)
        
        return result

class Strategy:
    
    def __init__(self, decision, selection, next):
        self.decision = decision
        self.selection = selection
        self.fitness = 0
        self.next = next
    
    def decide(self, config):
        if (len(self.next) == 0):
            return self.decision
        
        scale_result = config.use_scale(self.selection)
    
        return self.next[scale_result].decide(config)
    
    def duplicate(self):
        if (len(self.next) == 0):
            return Strategy(self.decision, None, [])
        
        else:
            selection = self.selection.duplicate()
            next_1 = self.next[0].duplicate()
            next_2 = self.next[1].duplicate()
            next_3 = self.next[2].duplicate()
            return Strategy(0, selection, [next_1, next_2, next_3])

    def test_correct(self, coins):
        configs = Config.generate_all(coins)
        for config in configs:
            if (self.decide(config) != config.fake_coin):
                return False
        
        return True
    
    def mutate(self, chance, coins):
        if (len(self.next) == 0):
            if (random_chance(chance)):
                self.decision = random.randint(0, coins - 1)
        
        else:
            self.selection.mutate(chance, coins)
            for next_strategy in self.next:
                next_strategy.mutate(chance, coins)
        
        self.autocorrect_all(coins)
    
    def autocorrect_all(self, coins):
        configs = Config.generate_all(coins)
        for config in configs:
            self.autocorrect(config, coins)
    
    def autocorrect(self, config, coins):
        if (len(self.next) == 0):
            self.decision = config.fake_coin
            return
        
        scale_result = config.use_scale(self.selection)
    
        self.next[scale_result].autocorrect(config, coins)
                
    #  def mutate_temp(self, chance, coins):
        #  if (len(self.next) == 0):
            #  if (random_chance(chance)):
                #  self.decision = random.randint(0, coins - 1)
        
        #  else:
            #  for next_strategy in self.next:
                #  next_strategy.mutate(chance, coins)
            
        #  self.autocorrect_all(coins)
    
    def __str__(self):
        return self.to_string("")
    
    def to_string(self, indent):
        if (len(self.next) == 0):
            return indent + "decision: " + str(self.decision) + "\n"
        
        else:
            return indent + str(self.selection) + "\n" + \
                indent + "if equal: [\n" + self.next[0].to_string(indent + "    ") + \
                indent + "]\n" + \
                indent + "if left heavy: [\n" + self.next[1].to_string(indent + "    ") + \
                indent + "]\n" + \
                indent + "if right heavy: [\n" + self.next[2].to_string(indent + "    ") + \
                indent + "]\n"
    
    def polish(self, ordering=None, known_equal=None):
        if (len(self.next) == 0):
            self.decision = ordering[self.decision]
            return
        
        if ordering == None:
            ordering = [0 for i in range(len(self.selection.data))]
            count = 0
            for i in range(len(self.selection.data)):
                if self.selection.data[i] == 1:
                    ordering[i] = count
                    count += 1
                    
            for i in range(len(self.selection.data)):
                if self.selection.data[i] == 2:
                    ordering[i] = count
                    count += 1
                    
            for i in range(len(self.selection.data)):
                if self.selection.data[i] == 0:
                    ordering[i] = count
                    count += 1
        
        if known_equal == None:
            known_equal = {}

        self.selection.polish(ordering, known_equal)
        
        known_equal_weighted   = known_equal.copy()
        known_equal_unweighted = known_equal.copy()
        
        for i in range(len(self.selection.data)):
            if self.selection.data[i] == 0:
                known_equal_unweighted[i] = True
                
            else:
                known_equal_weighted[i] = True
        
        for i in range(len(self.next)):
            if i == 0:
                self.next[i].polish(ordering, known_equal_weighted)
                
            else:
                self.next[i].polish(ordering, known_equal_unweighted)
    
    def cache_fitness(self, coins):
        configs = Config.generate_all(coins)
        
        deviation = 0.0
        
        for config in configs:
            deviation += abs(self.decide(config) - config.fake_coin)
        
        self.fitness = (1.0 / deviation) if deviation > 0.0 else 99999999.0
        
        return self.fitness

    def generate_random(tries, coins):
        result = None
        if (tries == 0):
            i = random.randint(0, coins - 1)
            result = Strategy(i, None, [])
        
        else:
            i = random.randint(1, (coins // 2))
            selection = Selection.generate_random(i, i, coins)
            #  if tries == 3: selection = Selection([1,1,1,1,2,2,2,2,0,0,0,0])
            #  else: selection = Selection.generate_random(i, i, coins)
            next_1 = Strategy.generate_random(tries - 1, coins)
            next_2 = Strategy.generate_random(tries - 1, coins)
            next_3 = Strategy.generate_random(tries - 1, coins)
            result = Strategy(0, selection, [next_1, next_2, next_3])
        
        result.autocorrect_all(coins)
        return result

    def generate_all(tries, coins):
        result = []
        if (tries == 0):
            for i in range(coins):
                result.append(Strategy(i, None, []))
        
        else:
            for i in range(1, (coins // 2) + 1):
                selections = Selection.generate_all(i, i, coins)
                next_1s = Strategy.generate_all(tries - 1, coins)
                next_2s = Strategy.generate_all(tries - 1, coins)
                next_3s = Strategy.generate_all(tries - 1, coins)
                for j in selections:
                    for k in next_1s:
                        for l in next_2s:
                            for m in next_3s:
                                result.append(Strategy(0, selections, [next_1s, next_2s, next_3s]))
        
        return result

#  Strategy.generate_all(3, 12)
#  print("hi")

POPULATION = 64
MUTATION_CHANCE = 0.05
TRIES = 3
COINS = 12
PAUSE = 1024

population = [Strategy.generate_random(TRIES, COINS) for i in range(POPULATION)]

generation = 1

#  a = Strategy.generate_random(TRIES, COINS)
#  print(str(a))
#  a.polish()
#  print(str(a))

#  input()

while True:
    #  if generation % PAUSE == 0: 
        #  input("Press enter to continue...")
        
    # evaluate, cache fitness, print result
    
    print("Generation: " + str(generation))
    
    max_fitness = 0
    max_fitness_org = None
    
    fitness_array = []
    
    for org in population:
        org.cache_fitness(COINS)
        if org.fitness > max_fitness:
            max_fitness = org.fitness
            max_fitness_org = org
        
        fitness_array.append(org.fitness)
    
    print("Max fitness: " + str(max_fitness))
    
    if max_fitness > 10:
        max_fitness_org.polish()
        print("- Solution: \n" + str(max_fitness_org))
        input("Solution found.")
        break;
        
    
    # make new population, mutate
    
    new_population = []
    for i in range(POPULATION):
        new_org = population[random_select_chance(fitness_array)].duplicate()
        #  new_org.mutate_temp(MUTATION_CHANCE, COINS)
        new_org.mutate(MUTATION_CHANCE, COINS)
        
        new_population.append(new_org)
    
    population = new_population
    
    generation += 1
