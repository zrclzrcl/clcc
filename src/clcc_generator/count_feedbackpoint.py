#注意，这里规定本脚本中使用的路径为绝对路径！并且无特殊情况路径的结尾是/如:/home'/'
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

class Normalizationer:
    def __init__(self):
        self._score_record = np.array([]) #记录所有的得分
        self._max_score = -10000.0     #得分最大值
        self._min_score = 10000.0     #得分最小值
        self._count = 0         #总分数计数
        self._avg = 0.0           #分数平均值
        self.median = 0.0         #分数中位数
        self._up4_score = 0.0     #上四分位点
        self._down4_score = 0.0   #下四分位点
        self._up1_score = 0.0     #上一分位点
        self._down1_score = 0.0   #下一分位点
        
    
    def __add_one_score(self,point_now):
        self._score_record = np.append(self._score_record, point_now)
        self._count += 1
        if self._score_record.size > 1000:
            recent_scores = self._score_record[-1000:]
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


        # if point_now < self._min_score:
        #     self._min_score = point_now
        # if point_now > self._max_score:
        #     self._max_score = point_now
        # self._avg = np.mean(self._score_record)
        # self.median = np.median(self._score_record)
        # self._down4_score = np.percentile(self._score_record, 25)
        # self._up4_score = np.percentile(self._score_record, 75)
        # self._down1_score = np.percentile(self._score_record, 10)
        # self._up1_score = np.percentile(self._score_record, 90)
    
    def get_down_k_tanh(self, target_point , middle, check_point, k): #给定一个指定的中间点，和一个数值，确保数值对应的tanh函数的斜率为指定值k 以此确定参数alpha
        def equation(target):
            return (target * np.cosh(target * (check_point - middle))**(-2)) - k
        alpha = fsolve(equation,0.5)
        alpha_set = alpha[0]
        normal_point = (np.tanh(alpha_set * (target_point - middle)) + 1)/2
        return normal_point


    def get_down_y_tanh(self, target_point , middle, check_point, y): #给定一个指定的中间点，和一个数值，确保数值对应的tanh函数的值为指定值y
        def equation(target):
            return ((np.tanh(target * (check_point - middle)) + 1) / 2) - y
        alpha = fsolve(equation,0.5)
        alpha_set = alpha[0]
        normal_point = (np.tanh(alpha_set * (target_point - middle)) + 1)/2
        return normal_point

    
    def get_normalization_point(self,point):
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
        else:
            
            down4_k_avg_middle = self.get_down_k_tanh(point, self._avg, self._down4_score, 0.1 )#以下4分位作为平缓点的得分
            down4_k_median_middle = self.get_down_k_tanh(point, self.median, self._down4_score, 0.1 )
            #以下一分为作为平缓点的得分
            down1_k_avg_middle = self.get_down_k_tanh(point, self._avg, self._down1_score, 0.1 )#以下4分位作为平缓点的得分
            down1_k_median_middle = self.get_down_k_tanh(point, self.median, self._down1_score, 0.1 )
            #以下一分为作为低分点的低分
            down1_y_avg_middle = self.get_down_y_tanh(point, self._avg, self._down1_score, 0.1 )#以下4分位作为平缓点的得分
            down1_y_median_middle = self.get_down_y_tanh(point, self.median, self._down1_score, 0.1 )
        return min_max_normal_point,down4_k_avg_middle,down4_k_median_middle,down1_k_avg_middle,down1_k_median_middle,down1_y_avg_middle,down1_y_median_middle
        #返回值依次是 最大最小值,下4平缓中平均值,下4平缓中中位，下1平缓中平均值,下1平缓中中位，下1低中平均值,下4低中中位

class DynamicIDAllocator:
    def __init__(self):
        self._recycled_ids = []       # 可回收ID堆
        self._max_id = 0              # 当前最大ID
        self._active_ids = set()      # 已分配ID集合
        self._lock = threading.Lock() # 线程锁
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
saved_count = 0
variable_lock = threading.Lock()


#获得单次showmap的cmd指令行
def get_showmap_cmd(showmap_path, showmap_out_path, testcase_id, showmap_testcase, target_db,config_path,mapsize):
    if target_db == 'sqlite':
        cmd = f'{showmap_path} -o {showmap_out_path}{testcase_id} -- /home/ossfuzz {showmap_testcase}'
    elif target_db == 'mysql':
        cmd = f'AFL_IGNORE_PROBLEMS=1 AFL_MAP_SIZE={mapsize} SQUIRREL_CONFIG="{config_path}" {showmap_path} -o {showmap_out_path}{testcase_id} -- /home/Squirrel/build_for_showmap/db_driver {showmap_testcase}'
    return cmd

#读取showmap对应id的内容
def get_showmap_content(showmap_out_path, testcase_id):
    result_dict = {}
    while True:
        try:
            with open(f"{showmap_out_path}{testcase_id}", "r") as f:
                for line in f:
                    key, value = line.strip().split(":")
                    result_dict[int(key)] = int(value)  # 假设值是数字，转换为整数
            break
        except:
            time.sleep(0.5)
            continue

    return result_dict

def get_prompt(samples,target_db,one_time_generete):
    prompt = f"""I want to perform fuzzy testing of {target_db} and need to generate test case for it. Please forget all database application background and generate complex and out-of-the-way {target_db} database test case from the point of view of a fuzzy testing expert, generate test cases that are complex and try to trigger database crashes as much as possible. Each testcase consists of several SQLs. Below I will give a sample test case that can trigger more program coverage:"""

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
    warp the generated test case. Now start generating sql testcase! Each testcase need have multiple sql. And just return the testcase! REMEMBER the purpose of generated testcase is to trigger crash in database!"""
    return prompt


#id 对应的测试用例id
#content 测试用例的内容
#showmap showmap的解析后字典
class ZrclTestcase:
    def __init__(self, testcase_id, content, showmap):
        self.id = testcase_id
        self.content = content
        self.showmap = showmap

#定义Map类用于计算覆盖率得分
class ZrclMap:
    def __init__(self,mapsize):
        self.countVectors = [0] * mapsize   #每条边的覆盖计数
        self.binaryVectors = [0] * mapsize  #每条边是否被命中的情况
        self.eachEdgeCovPoint = [0] * mapsize   #每条边计算的覆盖得分
        self.vectorNow = [0] * mapsize    #当前正在处理的向量
        self.mapSize = mapsize    #总Map大小
        self.uniqueEdge = 0 #当前覆盖的唯一边总数


    #使用当前情况计算每条边的得分
    def calculate_edgeCovPoint(self):
        for index, countVector in enumerate(self.countVectors):
            if self.uniqueEdge == 0:    #当初始冷启动的时候，权重都是0
                pass
            else:
                self.eachEdgeCovPoint[index]=math.log(self.uniqueEdge / (1+countVector), 10)/math.sqrt(self.mapSize)

    #确定对应边是否已有值
    def is_index_exist(self, index):
        return self.binaryVectors[index]

    #向向量中添加一个覆盖
    def append_to_vector(self, index):
        self.countVectors[index] += 1
        if not self.binaryVectors[index]:
            self.binaryVectors[index]=1
            self.uniqueEdge += 1

    #获得指定位置的情况
    def get_index_data(self, index):
        return self.countVectors[index], self.binaryVectors[index]

    #从测试用例类转化进入当前处理向量
    def from_zrclTestcase_get_vectorNow(self, zrcl_testcase:ZrclTestcase):
        for key,value in zrcl_testcase.showmap.items():   #将每一个命中的边加入map
            self.vectorNow[int(key)] = value

    #计算当前向量的得分
    def calculate_now_cov_get_point(self):
        get_point = 0
        for index, is_hits in enumerate(self.vectorNow):
            if is_hits:
                get_point += self.eachEdgeCovPoint[index]
        return get_point

    #重新计算新的每边得分
    def recalculate_each_edgeCovPoint(self):
        for index, is_hits in enumerate(self.vectorNow):
            if is_hits:
                self.append_to_vector(index)
        self.calculate_edgeCovPoint()
        self.vectorNow = [0] * self.mapSize



class ZrclSelectionQueue:
    def __init__(self):
        self.queueMaxLength = 10  # 最大个数
        self.lengthNow = 0  # 当前长度0开始计数
        self.selectTestcases=[ZrclTestcase(-1,None,None)] * self.queueMaxLength #保存的前MAX个测试用例
        self.pointQueue = [0] * self.queueMaxLength    #得分队列

    def order_selectTestcases(self):
        had_zip = zip(self.selectTestcases,self.pointQueue) #将两个队列组合成为元组
        after_sorted = sorted(had_zip,reverse=True,key=lambda x:x[1])#使用元组的point进行排序
        self.selectTestcases,self.pointQueue = list(zip(*after_sorted))
        self.selectTestcases = list(self.selectTestcases)
        self.pointQueue = list(self.pointQueue)


    def append_in(self, testcase, point):
        #无论怎么添加，都需要进行排序
        if self.lengthNow == self.queueMaxLength:#当前队列已满 进行剔除处理

            #1.对比当前的与最小的哪个最小，若不如最小的则剔除
            if point < self.pointQueue[self.lengthNow-1]:
                pass

            # 2.若比最小的大，则替换最小的，并排序
            else :
                self.pointQueue[self.lengthNow-1] = point
                self.selectTestcases[self.lengthNow-1] = testcase
                self.order_selectTestcases()

        #若队列没满 则直接加入到最后，并排序
        else :
            self.pointQueue[self.lengthNow] = point
            self.selectTestcases[self.lengthNow] = testcase
            self.lengthNow += 1
            self.order_selectTestcases()

    #用于弹出前3个测试用例，用于一次LLM调用样本
    def pop_one_combo(self):
        selected_testcases = []
        selected_testcases_to_str = []
        for i in range(0,3):
            if self.selectTestcases[i].id == -1:
                continue
            selected_testcases_to_str.append(self.selectTestcases[i].content)  #将前3个加入数组
            selected_testcases.append(self.selectTestcases[i])
        return selected_testcases,selected_testcases_to_str
    
    def delete_winsize(self,num_now,winsize):
        #基于当前窗口改变队列中过时的用例
        if num_now <= winsize:
            pass
        else:
            index = 0
            for each_testcase in self.selectTestcases:
                if each_testcase.id <= num_now-winsize:
                    self.selectTestcases[index] = ZrclTestcase(-1,None,None)
                    self.pointQueue[index] = 0
                    self.lengthNow -= 1
                index += 1
            self.order_selectTestcases()

#根据指定id获得完整文件名
def get_file_by_id(path, filename_prefix, current):
    # 构建文件名，假设文件名格式为 id_000000后接其他字符
    filename = f"{filename_prefix}{current:06d}*"  # 使用通配符匹配后缀
    file_path = os.path.join(path, filename)

    # 使用 glob 获取匹配的文件
    matched_files = glob.glob(file_path)

    # 如果找到匹配的文件，直接返回第一个文件的文件名
    if matched_files:
        with open(matched_files[0], "r") as file:
            content = file.read()
        return matched_files[0],content
    else:
        raise FileNotFoundError("文件不存在")

#不断产生ZrclTestcase的方法
#@myqueue 线程沟通的队列
#@testcase_path 测试用例所在的路径
#@showmap_path showmap工具所在的路径
#@showmap_out_path showmap输出结果保存的路径
def to_showmap(out_queue, testcase_path, showmap_path, showmap_out_path, target_db, config_path, mapsize):
    # ===================定义区===================
    current_id = 0  #记录当前的id
    cmd = ''    #保存需要执行的cmd
    showmap_stop_time = 0
    showmap_stop_num = 0
    first_time = True
    # ===================定义区===================
    print("showmap子线程启动")
    while True:
        try:    #尝试读取文件
            full_testcase_path, testcase_content = get_file_by_id(testcase_path,'id:',current_id)

        except FileNotFoundError as e:  #若目标文件还没有被生成
            if first_time:
                print(Fore.YELLOW + f"showmap子线程: 当前目标队列文件 {current_id} 还未被生成" + Style.RESET_ALL)
                first_time = False
                time.sleep(1)
            continue
        print(Fore.YELLOW+f"showmap子线程: 正在处理 {current_id} 文件"+Style.RESET_ALL)
        first_time = True
        #得到cmd路径
        cmd = get_showmap_cmd(showmap_path, showmap_out_path, current_id, full_testcase_path, target_db,config_path,mapsize)
        result = subprocess.run(cmd, shell=True, text=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        showmap_content = get_showmap_content(showmap_out_path, current_id)
        if target_db == 'mysql':
            while True:
                try:
                    with open("/home/for_showmap/showmap_server_pid.pid", "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()  # 读取第一行并去除首尾空格和换行符
                    result = subprocess.run(f"kill {first_line}", shell=True, text=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except:
                    time.sleep(0.1)
                    continue
        testcase_now = ZrclTestcase(current_id, testcase_content, showmap_content)
        out_queue.put(testcase_now)
        print(Fore.YELLOW + f"showmap子线程: {current_id} 文件的showmap结果已放入队列" + Style.RESET_ALL)
        current_id += 1


#LLM工作者方法，用于根据sample发送prompt,并保存响应的结果进入目标文件夹
#work_id 即发送的第几个prompt,用于作为文件后缀
#samples应为一个数组，里面是测试用例样本的内容
#model 定义使用的LLM模型
def llm_worker(samples, api_key, base_url, model, save_queue,target_db,one_time_generete):
    thread_id = allocator.acquire_id()
    try:
        print(Fore.LIGHTBLUE_EX + f"主动式大语言模型工作线程_{thread_id}:已启动，目前共有{allocator.active_count()}个主动线程正在运行。历史总计{allocator.total_allocated()}个" + Style.RESET_ALL)
        prompt = get_prompt(samples,target_db,one_time_generete)    #根据给定样本获取提示词
        start_time = time.time()
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_response =  client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        #将测试用例保存进入目标
        end_time = time.time()
        print(Fore.LIGHTBLUE_EX + f"主动式大语言模型工作线程_{thread_id}:生成结束，目前共有{allocator.active_count()}个主动线程正在运行。历史总计{allocator.total_allocated()}个 用时：{end_time-start_time:.2f}" + Style.RESET_ALL)
        save_queue.put(llm_response.choices[0].message.content)
    finally:
        allocator.release_id(thread_id)

def passively_llm_worker(selection_queue, api_key, base_url, model, save_queue,target_db,one_time_generete):
    global passively_llm_generate
    while True:
        start_time = time.time()
        testcases,samples = selection_queue.pop_one_combo()
        output = ''
        for testcases in testcases:
            output += ' ' + str(testcases.id)
        if output == '':
            output = '无'
        print(Fore.LIGHTGREEN_EX + f"被动式大语言模型工作线程_1: 使用了{output}" + Style.RESET_ALL)
        prompt = get_prompt(samples,target_db,one_time_generete)    #根据给定样本获取提示词
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_response =  client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        #将测试用例保存进入保存队列
        end_time = time.time()
        print(Fore.LIGHTGREEN_EX + f"被动式大语言模型工作线程_1: 使用了{output}，生成了第{passively_llm_generate+1}个测试用例。用时：{end_time-start_time:.2f}" + Style.RESET_ALL)
        save_queue.put(llm_response.choices[0].message.content)
        with variable_lock:
            passively_llm_generate += 1

def passively_llm_worker_2(selection_queue, api_key, base_url, model, save_queue,target_db,one_time_generete):
    global passively_llm_generate
    while True:
        start_time = time.time()
        testcases,samples = selection_queue.pop_one_combo()
        output = ''
        for testcases in testcases:
            output += ' ' + str(testcases.id)
        if output == '':
            output = '无'
        print(Fore.LIGHTGREEN_EX + f"被动式大语言模型工作线程_2: 使用了{output}" + Style.RESET_ALL)
        prompt = get_prompt(samples,target_db,one_time_generete)    #根据给定样本获取提示词
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_response =  client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        #将测试用例保存进入保存队列
        end_time = time.time()
        print(Fore.LIGHTGREEN_EX + f"被动式大语言模型工作线程_2: 使用了{output}，生成了第{passively_llm_generate+1}个测试用例。用时：{end_time-start_time:.2f}" + Style.RESET_ALL)
        save_queue.put(llm_response.choices[0].message.content)
        with variable_lock:
            passively_llm_generate += 1

def save_testcase(testcase_queue,save_path):
    #首先从队列获取测试用例
    #拿到测试用例并分割
    #保存分割后的测试用例进入目标文件夹
    global saved_count
    print("保存子线程已启动")
    while True:
        need_slice_testcase = testcase_queue.get()

        # 拿到测试用例并分割
        sql_cases = re.findall(r'```sql(.*?)```', need_slice_testcase, re.DOTALL)
        with variable_lock:
            for testcase in sql_cases:
                with open(f'{save_path}LLM_G_{saved_count+1}.txt', 'w') as file:
                    file.write(f'-- LLM Generated {saved_count+1}\n'+testcase.strip())
                    print(Fore.CYAN + f"保存子线程:当前第 {saved_count+1} 个LLM测试用例已生成" + Style.RESET_ALL)
                    saved_count += 1

def main():
    #===================定义区===================
   #LLM-apikey
    model = 'gpt-3.5-turbo' #LLM-模型
    base_url = 'https://api.zhizengzeng.com/v1/'    #LLM所在的基本地址
    testcase_path = "/tmp/fuzz/default/queue/" #定义测试用例文件地址
    showmap_path = "/home/Squirrel/AFLplusplus/afl-showmap"   #定义showmap工具的路径
    showmap_out_path = '/home/showmap/' #定义showmap的输出路径
    generate_testcase_save_path = '/home/LLM_testcase/'
    log_save_path = '/home/clcc_log/'
    showmap_queue_max_size = 10 #定义showmap子线程队列长度
    llm_queue_max_size = 50 #llm队列的最长个数
    save_queue = multiprocessing.Queue()  #保存需要保存为文件的测试用例分割前的队列
    testcase_queue = multiprocessing.Queue(maxsize=showmap_queue_max_size)    #定义showmap线程通信队列
    process_count = 0   #处理数记录
    llm_count = 0   #记录发送LLM请求的数量，以及保存生成的测试用例的后缀
    process_now = None  #保存当前记录的测试用例用于处理
    #实例化一个showmap
    select_testcase = ZrclSelectionQueue()  #实例化一个选择保存队列
    max_llm_workers = 5 #定义LLM线程池最大数量
    number_of_generate_testcase = 3 #定义每次调用生成多少个测试用例
    start_time = None #定义主过程阻塞开始时间
    end_time = None #定义主过程阻塞结束时间
    main_all_stop_time = 0  #主进程的阻塞总时间
    main_all_stop_num = 0   #主进程的阻塞总次数
    refresh_countdown = time.time() #记录上次发送时间
    last_save_time = time.time() #记录上次保存日志时间

    global passively_llm_generate
    global saved_count


    main_log_path = '/home/main_log/log.txt'
    main_count = 0
    #===================定义区===================
    parser = argparse.ArgumentParser(description="LLM生成器")
    parser.add_argument('-t', help='发送阈值设置', required=True,type=float)
    parser.add_argument('-db', help='目标数据库设置，可以是sqlite,mysql,postgresql,duckdb,mariadb', required=True)
    parser.add_argument('-o', help='单次请求生成的测试用例数',default=1)
    parser.add_argument('-k', help='LLM-apikey',required=True)
    parser.add_argument('-bu', help='LLM-baseurl',default='https://api.zhizengzeng.com/v1/')
    parser.add_argument('-mo', help='LLM-model',default='deepseek-reasoner')
    parser.add_argument('-conf', help='用于showmap的config文件，sqlite与duckdb不需要',required=True)
    parser.add_argument('-ms', help='mapsize大小，不知道请设为默认值65536',required=True,type=int)
    parser.add_argument('-norm', help='归一化方法选择 1：最大最小 2：下4分位平缓中平均值 3：下4分位中中位数 4：下1分位平缓中平均值 5：下1分位平缓中中位数 6：下1分位低中平均值 7：下1分位低中中位数',required=True,type=int,choices=[1, 2, 3, 4, 5, 6, 7],metavar='{1,2,3,4,5,6,7}')
    # 解析命令行参数
    args = parser.parse_args()
    
    threshold = args.t  #阈值设置
    target_db = args.db #目标数据库
    number_of_generate_testcase = args.o    #单次请求生成的测试用例数

    api_key = args.k    #定义LLM-apikey
    base_url = args.bu  #有默认值的基本url
    model = args.mo     #有默认值的模型
    showmap_config = args.conf #showmap的config文件
    map_size = args.ms  #mapsize大小
    norm_chose = args.norm  #归一化方法选择
    showmap = ZrclMap(map_size) #实例化一个showmap
    #===================主过程区===================

    init()

    
    #初始化，判断各路径是否存在，若不存在则创建文件夹
    if not Path(generate_testcase_save_path).exists():
        Path(generate_testcase_save_path).mkdir(parents=True)

    if not Path(showmap_out_path).exists():
        Path(showmap_out_path).mkdir(parents=True)

    if not Path(log_save_path).exists():
        Path(log_save_path).mkdir(parents=True)

    with open(log_save_path+"ccllm_log.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'passively_llm_generate', 'active_llm_generate', 'now_active_llm_worker', 'all_active_llm_worker', 'saved_count','process_count','meets_threshold'])

    with open(log_save_path+"point.csv", 'w', newline='', encoding='utf-8') as point_file:
        writer = csv.writer(point_file)
        writer.writerow(['time', 'id', 'ori_point','minmax_point','down4_k_avg_middle','down4_k_median_middle','down1_k_avg_middle','down1_k_median_middle','down1_y_avg_middle','down1_y_median_middle'])

    #初始化，输出区域


    saver_thread = multiprocessing.Process(target=save_testcase, args=(save_queue, generate_testcase_save_path), daemon=True)
    saver_thread.start()  # 保存子线程启动

    #showmap子线程配置
    showmap_thread = multiprocessing.Process(target=to_showmap, args=(testcase_queue, testcase_path, showmap_path, showmap_out_path,target_db,showmap_config,map_size), daemon=True)
    showmap_thread.start()  #showmap子线程启动

    pa_llm_thread = threading.Thread(target=passively_llm_worker, args=(
        select_testcase, api_key, base_url, model, save_queue,target_db,number_of_generate_testcase), daemon=True)
    pa_llm_thread.start()  #被动llm生成线程启动

    pa_llm_thread = threading.Thread(target=passively_llm_worker_2, args=(
        select_testcase, api_key, base_url, model, save_queue,target_db,number_of_generate_testcase), daemon=True)
    pa_llm_thread.start()  #被动llm生成线程启动


    my_normalization = Normalizationer()
    while True:
        #1.不断的取出队列中的测试用例进行处理
        process_now = testcase_queue.get()
        print(f"主程序:正在处理新的showmap数据 第 {main_count} 个")
        showmap.from_zrclTestcase_get_vectorNow(process_now)
        #2.对新的覆盖向量计算覆盖率得分,并尝试加入选择队列
        now_point = showmap.calculate_now_cov_get_point()
        min_max_normal_point,down4_k_avg_middle,down4_k_median_middle,down1_k_avg_middle,down1_k_median_middle,down1_y_avg_middle,down1_y_median_middle = my_normalization.get_normalization_point(now_point)
        #返回值依次是 最大最小值,下4平缓中平均值,下4平缓中中位，下1平缓中平均值,下1平缓中中位，下1低中平均值,下4低中中位
        
        if norm_chose == 1:
            norm_point = min_max_normal_point
        elif norm_chose == 2:
            norm_point = down4_k_avg_middle
        elif norm_chose == 3:
            norm_point = down4_k_median_middle
        elif norm_chose == 4:
            norm_point = down1_k_avg_middle
        elif norm_chose == 5:
            norm_point = down1_k_median_middle
        elif norm_chose == 6:
            norm_point = down1_y_avg_middle
        elif norm_chose == 7:
            norm_point = down1_y_median_middle

        print(f"主程序:第 {main_count} 个的得分为{now_point},归一化结果为{norm_point}")
 
        
        select_testcase.append_in(process_now, now_point)
        select_testcase.delete_winsize(main_count,1000)
        #3.更新覆盖率向量
        showmap.recalculate_each_edgeCovPoint()

        with open(log_save_path+"point.csv", 'a', newline='', encoding='utf-8') as point_file:
            writer = csv.writer(point_file)
            writer.writerow([time.time(), process_now.id , now_point,min_max_normal_point,down4_k_avg_middle,down4_k_median_middle,down1_k_avg_middle,down1_k_median_middle,down1_y_avg_middle,down1_y_median_middle])
        
        #当选择了一个队列长度的测试用例后，开始选择前3个测试用例，并发送给子线程
        #逻辑修改为，当得分超过阈值后，直接启动子线程
        if norm_point >= threshold:
            #这里就应该直接获取到指定id的测试用例
            now_content_list = [process_now.content]
            llm_thread = threading.Thread(target=llm_worker, args=(now_content_list, api_key, base_url, model ,save_queue,target_db,number_of_generate_testcase), daemon=True)
            llm_thread.start()
            llm_count += 1
            print(Fore.LIGHTYELLOW_EX + f"主程序: 第 {main_count} 个测试用例得分超过阈值，启动llm子线程，当前通过的总测试用例数为 {llm_count} 个" + Style.RESET_ALL)
        
        main_count += 1
        process_count += 1
        if (process_count % 5 == 0 ) or (time.time() - last_save_time > 10):
            with variable_lock:
                with open(log_save_path+"ccllm_log.csv", 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([time.time(), passively_llm_generate, allocator.total_allocated()*number_of_generate_testcase, allocator.active_count(), allocator.total_allocated(), saved_count, process_count, llm_count])
                    last_save_time = time.time()
        

    #===================主过程区===================

if __name__ == '__main__':
    main()
    #main(1) #测试用
