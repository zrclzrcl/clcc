# Note: use absolute paths in this script; paths typically end with a trailing slash (e.g., /home/).
import curses
import glob
import math
import os
import re
import subprocess
import threading
import time
from pathlib import Path
import multiprocessing
from openai import OpenAI
from colorama import Fore, Style,init
import argparse
import heapq
import threading
import csv
import time
from collections import defaultdict
import numpy as np
from scipy.optimize import fsolve
import socket

def is_port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        net_result = s.connect_ex((host, port))
        return net_result == 0  # Connection success means the port is in use.
    
class Normalizationer:
    def __init__(self,window):
        self._score_record = np.array([]) # record all scores
        self._max_score = -10000.0     # max score
        self._min_score = 10000.0     # min score
        self._count = 0         # total score count
        self._avg = 0.0           # score average
        self.median = 0.0         # score median
        self._up4_score = 0.0     # upper quartile
        self._down4_score = 0.0   # lower quartile
        self._up1_score = 0.0     # upper decile
        self._down1_score = 0.0   # lower decile
        self._window = window
        
    
    def __add_one_score(self,point_now):
        self._score_record = np.append(self._score_record, point_now)
        self._count += 1
        if self._score_record.size > self._window:
            recent_scores = self._score_record[-self._window:]
        else:
            recent_scores = self._score_record
        
        self._score_record = np.append(self._score_record,point_now)
        self._avg = np.mean(recent_scores)
        self.median = np.median(recent_scores)
        self._down4_score = np.percentile(recent_scores, 25)
        self._up4_score = np.percentile(recent_scores, 75)
        self._down1_score = np.percentile(recent_scores, 10)
        self._up1_score = np.percentile(recent_scores, 90)
        self._min_score = np.min(recent_scores)
        self._max_score = np.max(recent_scores)
    
    def get_down_k_tanh(self, target_point, middle, check_point, k):  # Given a midpoint and target slope k, solve for tanh alpha.
        def equation(target):
            if target < 0:
                target = -target
            return ((target / 2) * np.cosh(target * (check_point - middle)) ** (-2)) - k

        alpha = fsolve(equation, 0.5)
        alpha_set = alpha[0]
        if alpha_set < 0:
            alpha_set = -alpha_set
        normal_point = (np.tanh(alpha_set * (target_point - middle)) + 1) / 2
        return normal_point


    def get_down_y_tanh(self, target_point, middle, check_point, y):  # Given a midpoint and target y, solve for tanh alpha.
        def equation(target):
            if target < 0:
                target = -target
            return ((np.tanh(target * (check_point - middle)) + 1) / 2) - y

        alpha = fsolve(equation, 0.5)
        alpha_set = alpha[0]
        if alpha_set < 0:
            alpha_set = -alpha_set
        normal_point = (np.tanh(alpha_set * (target_point - middle)) + 1) / 2
        return normal_point

    
    def get_normalization_point(self,point):
        point_list = []
        self.__add_one_score(point)
        if self._count == 1 or self._max_score == self._min_score:
            min_max_normal_point = 1
        else:
            min_max_normal_point = (point - self._min_score)/(self._max_score - self._min_score)
        if self._count < 4:
            down4_k_avg_middle = 1
            down4_k_median_middle = 1
            down1_k_avg_middle = 1
            down1_k_median_middle = 1
            down1_y_avg_middle = 1
            down1_y_median_middle = 1
            down4_y_avg_middle=1
            down4_y_median_middle=1
            up4_y_avg_middle = 1
            up4_y_median_middle = 1
            up4_k_avg_middle = 1
            up4_k_median_middle = 1
            up1_y_avg_middle = 1
            up1_y_median_middle = 1
            up1_k_avg_middle = 1
            up1_k_median_middle = 1
        else:
            
            down4_k_avg_middle = self.get_down_k_tanh(point, self._avg, self._down4_score, 0.1)  # lower quartile as a gentle point
            down4_k_median_middle = self.get_down_k_tanh(point, self.median, self._down4_score, 0.1)
            
            # Lower quartile as a low-score point.
            down4_y_avg_middle = self.get_down_y_tanh(point, self._avg, self._down4_score, 0.25)  # lower quartile as a gentle point
            down4_y_median_middle = self.get_down_y_tanh(point, self.median, self._down4_score, 0.25)
            
            # Lower decile as a gentle point.
            down1_k_avg_middle = self.get_down_k_tanh(point, self._avg, self._down1_score, 0.1)  # lower quartile as a gentle point
            down1_k_median_middle = self.get_down_k_tanh(point, self.median, self._down1_score, 0.1)
            # Lower decile as a low-score point.
            down1_y_avg_middle = self.get_down_y_tanh(point, self._avg, self._down1_score, 0.1)  # lower quartile as a gentle point
            down1_y_median_middle = self.get_down_y_tanh(point, self.median, self._down1_score, 0.1)


            up4_y_avg_middle = self.get_down_y_tanh(point, self._avg, self._up4_score, 0.75)  # upper quartile as a gentle point
            up4_y_median_middle = self.get_down_y_tanh(point, self.median, self._up4_score, 0.75)
            
            
            up4_k_avg_middle = self.get_down_k_tanh(point, self._avg, self._up4_score, 0.1)  # upper quartile as a gentle point
            up4_k_median_middle = self.get_down_k_tanh(point, self.median, self._up4_score, 0.1)

            up1_y_avg_middle = self.get_down_y_tanh(point, self._avg, self._up1_score, 0.9)  # upper decile as a gentle point
            up1_y_median_middle = self.get_down_y_tanh(point, self.median, self._up1_score, 0.9)

            up1_k_avg_middle = self.get_down_k_tanh(point, self._avg, self._up1_score, 0.1)  # upper decile as a gentle point
            up1_k_median_middle = self.get_down_k_tanh(point, self.median, self._up1_score, 0.1)
            
        
        point_list.append(min_max_normal_point)
        
        point_list.append(down4_k_avg_middle)
        point_list.append(down4_k_median_middle)
        point_list.append(down4_y_avg_middle)
        point_list.append(down4_y_median_middle)

        point_list.append(down1_k_avg_middle)
        point_list.append(down1_k_median_middle)
        point_list.append(down1_y_avg_middle)
        point_list.append(down1_y_median_middle)

        point_list.append(up4_k_avg_middle)
        point_list.append(up4_k_median_middle)
        point_list.append(up4_y_avg_middle)
        point_list.append(up4_y_median_middle)

        point_list.append(up1_k_avg_middle)
        point_list.append(up1_k_median_middle)
        point_list.append(up1_y_avg_middle)
        point_list.append(up1_y_median_middle)
        return point_list
        # Return order:
        # min-max normalization,
        # lower-4th: k avg, k median, y avg, y median,
        # lower-1st: k avg, k median, y avg, y median,
        # upper-4th: k avg, k median, y avg, y median,
        # upper-1st: k avg, k median, y avg, y median.

class DynamicIDAllocator:
    def __init__(self):
        self._recycled_ids = []       # recycled ID heap
        self._max_id = 0              # current max ID
        self._active_ids = set()      # allocated ID set
        self._lock = threading.Lock() # thread lock
        self._total_allocated = 0 
        heapq.heapify(self._recycled_ids)

    def active_count(self) -> int:
        with self._lock:
            return len(self._active_ids)
        
    def acquire_id(self) -> int:
        with self._lock:
            self._total_allocated += 1
            if self._recycled_ids:
                new_id = heapq.heappop(self._recycled_ids)
            else:
                new_id = self._max_id
                self._max_id += 1
            self._active_ids.add(new_id)
            return new_id
    
    def release_id(self, id_num: int) -> None:
        with self._lock:
            if id_num in self._active_ids:
                self._active_ids.remove(id_num)
                heapq.heappush(self._recycled_ids, id_num)

    def total_allocated(self):
        with self._lock:
            return self._total_allocated

allocator = DynamicIDAllocator()
passively_llm_generate = 0
passively_llm_generate_lock = threading.Lock()

variable_lock = threading.Lock()


# Build the showmap command line for a single run.
def get_showmap_cmd(showmap_path, showmap_out_path, testcase_id, showmap_testcase, target_db,config_path,mapsize):
    if target_db == 'sqlite':
        cmd = f'{showmap_path} -o {showmap_out_path}{testcase_id} -- /home/ossfuzz {showmap_testcase}'
    if target_db == 'duckdb':
        cmd = f'AFL_MAP_SIZE={mapsize} {showmap_path} -o {showmap_out_path}{testcase_id} -- /home/duckdb/build/release/duckdb -f {showmap_testcase}'
    elif target_db == 'mysql':
        cmd = f'AFL_IGNORE_PROBLEMS=1 AFL_MAP_SIZE={mapsize} SQUIRREL_CONFIG="{config_path}" {showmap_path} -o {showmap_out_path}{testcase_id} -- /home/Squirrel/build_for_showmap/db_driver {showmap_testcase}'
    elif target_db == 'mariadb':
        cmd = f'AFL_MAP_SIZE={mapsize} SQUIRREL_CONFIG="{config_path}" {showmap_path} -o {showmap_out_path}{testcase_id} -- /home/Squirrel/build_for_showmap/db_driver {showmap_testcase}'
    elif target_db == 'postgresql':
        cmd = f'AFL_IGNORE_PROBLEMS=1 AFL_MAP_SIZE={mapsize} SQUIRREL_CONFIG="{config_path}" {showmap_path} -o {showmap_out_path}{testcase_id} -- /home/Squirrel/build_for_showmap/db_driver {showmap_testcase}'
    return cmd

# Read the showmap output for a given id.
def get_showmap_content(showmap_out_path, testcase_id):
    result_dict = {}
    while True:
        try:
            with open(f"{showmap_out_path}{testcase_id}", "r") as f:
                for line in f:
                    key, value = line.strip().split(":")
                    result_dict[int(key)] = int(value)  # assume values are numeric
            break
        except:
            time.sleep(0.5)
            continue

    return result_dict

def get_prompt(samples,target_db,target_version,one_time_generete):
    prompt = f"""I want to perform fuzzy testing of {target_db} (version {target_version}) and need to generate test case for it. Please forget all database application background and generate complex and out-of-the-way {target_db} database test case from the point of view of a fuzzy testing expert, generate test cases that are complex and try to trigger database crashes as much as possible. Each testcase consists of several SQLs. Below I will give a sample test case that can trigger more program coverage:"""

    for sample in samples:
        prompt += f"\n```sql\n{sample}\n```"

    prompt += f"""\nYou can refer to the test case I gave, add more contents base on the samples. And generate more test case randomly. It is not only important to refer to the test case I have given, but it is also important to think about the process of generating them according to the procedure I have given below.
    First of all, you need to make sure that the SQL syntax is correct when generating the test case.
    Second, whether the generated test case have sufficient statement diversity, the generated testcase need contain SQL key word as mach as possible.
    Third, it is very important that the generated test case test the functionality that the target database has and other databases do not. If not, it needs to be added to the testcase.
    Fourth, is the generated SQL complex enough, at least it's more complex than the structure of the sample I gave you.
    Fifth, check whether the SQL is semantically correct, and whether there is corresponding data in it to be manipulated, and if not, then create the insert data statement first to ensure that the statement can be successfully executed.
    Note that the generated statements must be very complex. Include multiple nesting with the use of functions, you can also create functions for testing!
    Based on the above description, you can start generating {one_time_generete} test cases and start them with
    ```sql
    ```
    warp the generated test case. Now start generating sql testcase! Each testcase need have multiple sql. And just return the testcase! REMEMBER the purpose of generated testcase is to trigger crash in database! Not generate testcase contain infinite loop or database operations that will take a long time to execute."""
    return prompt


# id: testcase id
# content: testcase content
# showmap: parsed showmap dict
class ZrclTestcase:
    def __init__(self, testcase_id, content, showmap):
        self.id = testcase_id
        self.content = content
        self.showmap = showmap

# Map class for coverage scoring.
class ZrclMap:
    def __init__(self,mapsize):
        self.countVectors = [0] * mapsize   # per-edge hit counts
        self.binaryVectors = [0] * mapsize  # per-edge hit flag
        self.eachEdgeCovPoint = [0] * mapsize   # per-edge coverage score
        self.vectorNow = [0] * mapsize    # current vector under processing
        self.mapSize = mapsize    # total map size
        self.uniqueEdge = 0 # total unique edges covered


    # Compute per-edge scores from current counts.
    def calculate_edgeCovPoint(self):
        for index, countVector in enumerate(self.countVectors):
            if self.uniqueEdge == 0:    # cold start: all weights are 0
                pass
            else:
                self.eachEdgeCovPoint[index]=math.log(self.uniqueEdge / (1+countVector), 10)/math.sqrt(self.mapSize)

    # Check whether an edge has been hit.
    def is_index_exist(self, index):
        return self.binaryVectors[index]

    # Add a hit to the vector.
    def append_to_vector(self, index):
        self.countVectors[index] += 1
        if not self.binaryVectors[index]:
            self.binaryVectors[index]=1
            self.uniqueEdge += 1

    # Get data for the given index.
    def get_index_data(self, index):
        return self.countVectors[index], self.binaryVectors[index]

    # Load hits from testcase into current vector.
    def from_zrclTestcase_get_vectorNow(self, zrcl_testcase:ZrclTestcase):
        for key,value in zrcl_testcase.showmap.items():   # add each hit edge to the map
            self.vectorNow[int(key)] = value

    # Compute the score for the current vector.
    def calculate_now_cov_get_point(self):
        get_point = 0
        for index, is_hits in enumerate(self.vectorNow):
            if is_hits:
                get_point += self.eachEdgeCovPoint[index]
        return get_point

    # Recompute per-edge scores.
    def recalculate_each_edgeCovPoint(self):
        for index, is_hits in enumerate(self.vectorNow):
            if is_hits:
                self.append_to_vector(index)
        self.calculate_edgeCovPoint()
        self.vectorNow = [0] * self.mapSize



class ZrclSelectionQueue:
    def __init__(self):
        self.queueMaxLength = 10  # max size
        self.lengthNow = 0  # current length (0-based)
        self.selectTestcases=[ZrclTestcase(-1,None,None)] * self.queueMaxLength # top MAX testcases
        self.pointQueue = [0] * self.queueMaxLength    # score queue

    def order_selectTestcases(self):
        had_zip = zip(self.selectTestcases,self.pointQueue) # combine into tuples
        after_sorted = sorted(had_zip,reverse=True,key=lambda x:x[1])# sort by score
        self.selectTestcases,self.pointQueue = list(zip(*after_sorted))
        self.selectTestcases = list(self.selectTestcases)
        self.pointQueue = list(self.pointQueue)


    def append_in(self, testcase, point):
        # Always sort after insert.
        if self.lengthNow >= self.queueMaxLength-1:# queue full, consider eviction
            self.lengthNow = self.queueMaxLength-1
            # 1) if worse than the smallest, drop it
            if point < self.pointQueue[self.lengthNow]:
                pass

            # 2) else replace the smallest and sort
            else :
                self.pointQueue[self.lengthNow] = point
                self.selectTestcases[self.lengthNow] = testcase
                self.order_selectTestcases()

        # If queue not full, append and sort.
        else :
            print("Current queue length",self.lengthNow)
            self.pointQueue[self.lengthNow] = point
            self.selectTestcases[self.lengthNow] = testcase
            self.lengthNow += 1
            self.order_selectTestcases()

    # Pop top 3 testcases as LLM samples.
    def pop_one_combo(self):
        selected_testcases = []
        selected_testcases_to_str = []
        for i in range(0,3):
            if self.selectTestcases[i].id == -1:
                continue
            selected_testcases_to_str.append(self.selectTestcases[i].content)  # add top 3 to list
            selected_testcases.append(self.selectTestcases[i])
        return selected_testcases,selected_testcases_to_str
    
    def delete_winsize(self,num_now,winsize):
        # Drop stale testcases based on window size.
        if num_now <= winsize:
            pass
        else:
            index = 0
            for each_testcase in self.selectTestcases:
                if each_testcase.id <= num_now-winsize and each_testcase.id != -1:
                    self.selectTestcases[index] = ZrclTestcase(-1,None,None)
                    self.pointQueue[index] = 0
                    self.lengthNow = self.lengthNow - 1
                index += 1
            self.order_selectTestcases()

# Get full filename by testcase id.
def get_file_by_id(path, filename_prefix, current):
    # Build filename, assuming id_000000 prefix.
    filename = f"{filename_prefix}{current:06d}*"  # match any suffix with a wildcard
    file_path = os.path.join(path, filename)

    # Use glob to find matches.
    matched_files = glob.glob(file_path)

    # Return the first match if found.
    if matched_files:
        with open(matched_files[0], "r") as file:
            content = file.read()
        return matched_files[0],content
    else:
        raise FileNotFoundError("file not found")

# Continuously generate ZrclTestcase objects.
# @myqueue: thread communication queue
# @testcase_path: testcase directory
# @showmap_path: showmap binary path
# @showmap_out_path: showmap output directory
def to_showmap(out_queue, testcase_path, showmap_path, showmap_out_path, target_db, config_path, mapsize):
    # ===================definitions===================
    current_id = 0  # current id
    cmd = ''    # command to run
    showmap_stop_time = 0
    showmap_stop_num = 0
    first_time = True
    # ===================definitions===================
    print("Showmap worker started")
    while True:
        try:    # try to read file
            full_testcase_path, testcase_content = get_file_by_id(testcase_path,'id:',current_id)

        except FileNotFoundError as e:  # target file not generated yet
            if first_time:
                print(Fore.YELLOW + f"showmap worker: target queue file {current_id} not generated yet" + Style.RESET_ALL)
                first_time = False
                time.sleep(1)
            continue
        print(Fore.YELLOW+f"showmap worker: processing file {current_id}"+Style.RESET_ALL)
        first_time = True
        # build cmd
        cmd = get_showmap_cmd(showmap_path, showmap_out_path, current_id, full_testcase_path, target_db,config_path,mapsize)
        result = subprocess.run(cmd, shell=True, text=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        showmap_content = get_showmap_content(showmap_out_path, current_id)
        if target_db == 'mysql':
            while True:
                try:
                    with open("/home/for_showmap/showmap_server_pid.pid", "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()  # read first line and strip whitespace
                    result = subprocess.run(f"kill {first_line}", shell=True, text=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except:
                    time.sleep(0.1)
                    continue
        if target_db == 'mariadb':
            while True:
                try:
                    with open("/home/for_showmap/showmap_server_pid.pid", "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()  # read first line and strip whitespace
                    result = subprocess.run(f"kill {first_line}", shell=True, text=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except:
                    time.sleep(0.1)
                    continue
        if target_db == 'postgresql':
            while True:
                try:
                    with open("/home/for_showmap/pgsql/data/postmaster.pid", "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()  # read first line and strip whitespace
                    result = subprocess.run(f"kill {first_line}", shell=True, text=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except:
                    if is_port_in_use("127.0.0.1",5433):
                        time.sleep(0.1)
                        continue
                    else:
                        break
        testcase_now = ZrclTestcase(current_id, testcase_content, showmap_content)
        out_queue.put(testcase_now)
        print(Fore.YELLOW + f"showmap worker: showmap result for file {current_id} enqueued" + Style.RESET_ALL)
        current_id += 1


# LLM worker: send prompts from samples and save responses.
# work_id: prompt index used as file suffix
# samples: list of testcase sample contents
# model: LLM model name
def llm_worker(samples, api_key, base_url, model, save_queue,target_db,target_version,one_time_generete, llm_semaphore=None):
    thread_id = allocator.acquire_id()
    try:
        print(Fore.LIGHTBLUE_EX + f"Active LLM worker_{thread_id}: started, {allocator.active_count()} active workers running. Total allocated {allocator.total_allocated()}" + Style.RESET_ALL)
        prompt = get_prompt(samples,target_db,target_version,one_time_generete)    # build prompt from samples
        start_time = time.time()
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_response =  client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        # Save testcase to target.
        end_time = time.time()
        print(Fore.LIGHTBLUE_EX + f"Active LLM worker_{thread_id}: generation finished, {allocator.active_count()} active workers running. Total allocated {allocator.total_allocated()} Time: {end_time-start_time:.2f}" + Style.RESET_ALL)
        save_queue.put(llm_response.choices[0].message.content)
    finally:
        allocator.release_id(thread_id)
        if llm_semaphore is not None:
            llm_semaphore.release()

def passively_llm_worker(selection_queue, api_key, base_url, model, save_queue,target_db,target_version,one_time_generete,worker_id):
    global passively_llm_generate
    while True:
        try:
            start_time = time.time()
            testcases,samples = selection_queue.pop_one_combo()
            output = ''
            for testcases in testcases:
                output += ' ' + str(testcases.id)
            if output == '':
                output = 'none'
            print(Fore.LIGHTGREEN_EX + f"Passive LLM worker_{worker_id}: used{output}" + Style.RESET_ALL)
            prompt = get_prompt(samples,target_db,target_version,one_time_generete)    # build prompt from samples
            client = OpenAI(api_key=api_key, base_url=base_url)
            llm_response =  client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            # Save testcase into save queue.
            end_time = time.time()
            print(Fore.LIGHTGREEN_EX + f"Passive LLM worker_{worker_id}: used{output}, generated testcase #{passively_llm_generate+1}. Time: {end_time-start_time:.2f}" + Style.RESET_ALL)
            save_queue.put(llm_response.choices[0].message.content)
            with variable_lock:
                passively_llm_generate += 1
        except:
            with variable_lock:
                print(Fore.LIGHTGREEN_EX + f"Passive LLM worker_{worker_id}: error generating testcase #{passively_llm_generate+1}! API call limit may be reached; check quota or retry later." + Style.RESET_ALL)
            continue



def save_testcase(testcase_queue,save_path,saved_count,ban_testcase_count,ban_testcse_path):
    def is_abandoned_testcase(testcase):
        abandon_word = [
            'CREATE DATABASE',
            'infinite_loop',
            'infinite loop',
            'sleep',
            'CREATE USER',
            'ALTER USER',
            'SYSTEM shutdown'
        ]
        for word in abandon_word:
            if word in testcase or word.upper() in testcase or word.lower() in testcase or word.capitalize() in testcase or word.title() in testcase or word.swapcase() in testcase:
                return True,word
        return False,None
    # Fetch testcases from queue, split, and save.
    print("Saver worker started")
    while True:
        need_slice_testcase = testcase_queue.get()
        # Split testcases.
        sql_cases = re.findall(r'```sql(.*?)```', need_slice_testcase, re.DOTALL)
        with saved_count.get_lock():
            for testcase in sql_cases:
                flag,why = is_abandoned_testcase(testcase)
                if flag:
                    with ban_testcase_count.get_lock():
                        ban_testcase_count.value += 1
                        with open(f'{ban_testcse_path}LLM_{why}_BAN_{ban_testcase_count.value}.txt', 'w') as file:
                            file.write(f'-- LLM Generated {ban_testcase_count.value}\n'+testcase.strip())
                        print(Fore.RED + f"Saver worker: testcase #{ban_testcase_count.value} discarded" + Style.RESET_ALL)
                        continue
                # Save split testcase into target folder.
                with open(f'{save_path}LLM_G_{saved_count.value+1}.txt', 'w') as file:
                    file.write(f'-- LLM Generated {saved_count.value+1}\n'+testcase.strip())
                    print(Fore.CYAN + f"Saver worker: LLM testcase #{saved_count.value+1} generated" + Style.RESET_ALL)
                    saved_count.value += 1

def main():
    #===================definitions===================
   # LLM api key
    model = 'gpt-3.5-turbo' # LLM model
    base_url = 'https://api.zhizengzeng.com/v1/'    # LLM base URL
    testcase_path = "/tmp/fuzz/default/queue/" # testcase directory
    showmap_path = "/home/Squirrel/AFLplusplus/afl-showmap"   # showmap binary path
    showmap_out_path = '/home/showmap/' # showmap output directory
    generate_testcase_save_path = '/home/LLM_testcase/'
    ban_testcase_path = '/home/ban_testcase/' # discarded testcase output directory
    log_save_path = '/home/clcc_log/'
    showmap_queue_max_size = 10 # showmap queue length
    llm_queue_max_size = 50 # max length of llm queue
    save_queue = multiprocessing.Queue()  # queue of testcases to save (pre-split)
    testcase_queue = multiprocessing.Queue(maxsize=showmap_queue_max_size)    # showmap thread queue
    process_count = 0   # processed count
    llm_count = 0   # LLM request count (and testcase suffix)
    process_now = None  # current testcase for processing
    # instantiate selection queue
    select_testcase = ZrclSelectionQueue()  # selection queue
    number_of_generate_testcase = 3 # testcases per request
    start_time = None # main loop block start time
    end_time = None # main loop block end time
    main_all_stop_time = 0  # total main process block time
    main_all_stop_num = 0   # total main process block count
    refresh_countdown = time.time() # last send time
    last_save_time = time.time() # last log save time

    global passively_llm_generate
    saved_count = multiprocessing.Value('i', 0) 
    ban_testcase_count = multiprocessing.Value('i', 0) 

    main_count = 0
    #===================definitions===================
    parser = argparse.ArgumentParser(description="LLM generator")
    parser.add_argument('-t', help='send threshold', required=True,type=float)
    parser.add_argument('-db', help='target DB: sqlite,mysql,postgresql,duckdb,mariadb', required=True)
    parser.add_argument('-v', help='target DB version', required=True)
    parser.add_argument('-o', help='testcases per request',default=1)
    parser.add_argument('-k', help='LLM apikey',required=True)
    parser.add_argument('-bu', help='LLM baseurl',required=True)
    parser.add_argument('-mo', help='LLM model',required=True)
    parser.add_argument('-conf', help='showmap config (not needed for sqlite/duckdb)',required=True)
    parser.add_argument('-ms', help='mapsize (use 65536 if unsure)',required=True,type=int)
    parser.add_argument('-norm', help='normalization method 1:min-max 2:lower-4th k avg 3:lower-4th k median 4:lower-1st k avg 5:lower-1st k median 6:lower-1st y avg 7:lower-1st y median',required=True,type=int,choices=[1, 2, 3, 4, 5, 6, 7,8,9,10,11,12,13,14,15,16,17],metavar='{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17}')
    parser.add_argument('-pn', help='number of passive LLM workers',required=True,type=int)
    parser.add_argument('-maxw', help='max active LLM workers', default=100, type=int)
    parser.add_argument('-win', help='window size',required=True,type=int)
    # Parse CLI args.
    args = parser.parse_args()
    
    threshold = args.t  # threshold
    target_db = args.db # target db
    target_version = args.v # target db version
    number_of_generate_testcase = int(args.o)    # testcases per request

    api_key = args.k    # LLM api key
    base_url = args.bu  # base url (has default)
    model = args.mo     # model (has default)
    showmap_config = args.conf # showmap config
    map_size = args.ms  # mapsize
    norm_chose = args.norm  # normalization method
    showmap = ZrclMap(map_size) # instantiate showmap
    passively_llm_worker_num = args.pn # passive LLM worker count
    max_llm_workers = args.maxw
    window = args.win   # window size
    #===================main loop===================

    init()
    llm_semaphore = threading.Semaphore(max_llm_workers)

    
    # Ensure output directories exist.
    if not Path(generate_testcase_save_path).exists():
        Path(generate_testcase_save_path).mkdir(parents=True)

    if not Path(showmap_out_path).exists():
        Path(showmap_out_path).mkdir(parents=True)

    if not Path(log_save_path).exists():
        Path(log_save_path).mkdir(parents=True)

    if not Path(ban_testcase_path).exists():
        Path(ban_testcase_path).mkdir(parents=True)

    with open(log_save_path+"ccllm_log.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'passively_llm_generate', 'active_llm_generate', 'now_active_llm_worker', 'all_active_llm_worker', 'saved_count','process_count','meets_threshold','ban_testcase_count'])

    with open(log_save_path+"point.csv", 'w', newline='', encoding='utf-8') as point_file:
        writer = csv.writer(point_file)
        writer.writerow(['time', 'id', 'ori_point','min_max_normal_point','down4_k_avg_middle','down4_k_median_middle','down4_y_avg_middle','down4_y_median_middle','down1_k_avg_middle','down1_k_median_middle','down1_y_avg_middle','down1_y_median_middle','up4_k_avg_middle','up4_k_median_middle','up4_y_avg_middle','up4_y_median_middle','up1_k_avg_middle','up1_k_median_middle','up1_y_avg_middle','up1_y_median_middle'])

    # Init output region.


    saver_thread = multiprocessing.Process(target=save_testcase, args=(save_queue, generate_testcase_save_path, saved_count, ban_testcase_count,ban_testcase_path), daemon=True)
    saver_thread.start()  # saver thread

    # showmap thread
    showmap_thread = multiprocessing.Process(target=to_showmap, args=(testcase_queue, testcase_path, showmap_path, showmap_out_path,target_db,showmap_config,map_size), daemon=True)
    showmap_thread.start()  # showmap thread start

    i=1
    while i <= passively_llm_worker_num:
        pa_llm_thread = threading.Thread(target=passively_llm_worker, args=(
        select_testcase, api_key, base_url, model, save_queue,target_db,target_version,number_of_generate_testcase, i), daemon=True)
        pa_llm_thread.start() 
        i += 1


    my_normalization = Normalizationer(window)
    while True:
        # 1) process testcase from queue
        process_now = testcase_queue.get()
        print(f"Main: processing new showmap data #{main_count}")
        showmap.from_zrclTestcase_get_vectorNow(process_now)
        # 2) compute coverage score and try to enqueue
        now_point = showmap.calculate_now_cov_get_point()
        point_list = my_normalization.get_normalization_point(now_point)
        # Return order:
        # min-max normalization,
        # lower-4th: k avg, k median, y avg, y median,
        # lower-1st: k avg, k median, y avg, y median,
        # upper-4th: k avg, k median, y avg, y median,
        # upper-1st: k avg, k median, y avg, y median.

        norm_point = point_list[norm_chose-1]

        print(f"Main: score for #{main_count} is {now_point}, normalized result {norm_point}")
 
        
        select_testcase.append_in(process_now, now_point)
        select_testcase.delete_winsize(main_count,window)
        # 3) update coverage vector
        showmap.recalculate_each_edgeCovPoint()

        with open(log_save_path+"point.csv", 'a', newline='', encoding='utf-8') as point_file:
            writer = csv.writer(point_file)
            writer.writerow([time.time(), process_now.id , now_point, point_list[0],point_list[1],point_list[2],point_list[3],point_list[4],point_list[5],point_list[6],point_list[7],point_list[8],point_list[9],point_list[10],point_list[11],point_list[12],point_list[13],point_list[14],point_list[15],point_list[16]])
        
        # When score exceeds threshold, start an LLM worker.
        if norm_point >= threshold:
            # Use the current testcase directly.
            now_content_list = [process_now.content]
            llm_semaphore.acquire()
            llm_thread = threading.Thread(target=llm_worker, args=(now_content_list, api_key, base_url, model ,save_queue,target_db,target_version,number_of_generate_testcase, llm_semaphore), daemon=True)
            llm_thread.start()
            llm_count += 1
            print(Fore.LIGHTYELLOW_EX + f"Main: testcase #{main_count} exceeded threshold, starting LLM worker, total passed {llm_count}" + Style.RESET_ALL)
        
        main_count += 1
        process_count += 1
        if (process_count % 5 == 0 ) or (time.time() - last_save_time > 5):
            with variable_lock:
                with open(log_save_path+"ccllm_log.csv", 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    with ban_testcase_count.get_lock():
                        writer.writerow([time.time(), passively_llm_generate, allocator.total_allocated()*number_of_generate_testcase, allocator.active_count(), allocator.total_allocated(), saved_count.value, process_count, llm_count, ban_testcase_count.value])
                    last_save_time = time.time()
        

    #===================main loop===================

if __name__ == '__main__':
    main()
    #main(1) # for testing
