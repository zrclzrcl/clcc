#include <cassert>
#include <fstream>
#include <iostream>
#include <memory>
#include <stack>
#include <string>
#include <stdio.h>
#include "afl-fuzz.h"
#include "config_validate.h"
#include "db.h"
#include "env.h"
#include "yaml-cpp/yaml.h"

struct ZrclMutator {
	ZrclMutator() : fuzz_now(0),fuzz_next(1) {				// 初始化 fuzz_now 为 0
		strcpy(LLM_in_dir, "/home/LLM_testcase/");  // 使用 strcpy 初始化字符数组
	}
	~ZrclMutator() {
		// 如果有需要清理的资源，可以在这里处理
		// 目前没有需要清理的动态资源
	}
  bool zrcl_is_have_new_in();
	char LLM_in_dir[50];
	int fuzz_now;
	int fuzz_next;
};

struct SquirrelMutator {
  SquirrelMutator(DataBase *db) : database(db),select(false) {}
  ~SquirrelMutator() { delete database; }
  DataBase *database;
  std::string current_input;
  ZrclMutator zrcl_mutator; //zrcl的模糊器扩展
  bool select; //用于模糊器的选择，false为zrcl_mutator,ture为Squirrel变异器
};

//----------------FROM RICHARD ZHANG-----------------
bool ZrclMutator::zrcl_is_have_new_in() {
    char LLM_in_path[100] = {0};  // 确保路径缓冲区足够大，并且初始化为0
    char file_name[50] = {0};     // 初始化文件名缓冲区

    // 拼接文件名并格式化路径
    snprintf(file_name, sizeof(file_name), "LLM_G_%d.txt", fuzz_next);  // 使用 snprintf 格式化文件名
    snprintf(LLM_in_path, sizeof(LLM_in_path), "%s%s", LLM_in_dir, file_name);  // 拼接完整路径

    // 使用 access 函数检查文件是否存在
    if (access(LLM_in_path, F_OK) == 0) {
        // 文件存在
        return true;
    } else {
        // 文件不存在
        return false;
    }
}
//----------------END OF RICHARD ZHANG---------------


extern "C" {

void *afl_custom_init(afl_state_t *afl, unsigned int seed) {
  const char *config_file_path = getenv(kConfigEnv);
  if (!config_file_path) {
    std::cerr << "You should set the enviroment variable " << kConfigEnv
              << " to the path of your config file." << std::endl;
    exit(-1);
  }
  std::string config_file(config_file_path);
  std::cerr << "Config file: " << config_file << std::endl;
  YAML::Node config = YAML::LoadFile(config_file);
  if (!utils::validate_db_config(config)) {
    std::cerr << "Invalid config!" << std::endl;
  }
  auto *mutator = create_database(config);
  return new SquirrelMutator(mutator);
}

void afl_custom_deinit(SquirrelMutator *data) { delete data; }

u8 afl_custom_queue_new_entry(SquirrelMutator *mutator,
                              const unsigned char *filename_new_queue,
                              const unsigned char *filename_orig_queue) {
  // read a file by file name
  std::ifstream ifs((const char *)filename_new_queue);
  std::string content((std::istreambuf_iterator<char>(ifs)),
                      (std::istreambuf_iterator<char>()));
  mutator->database->save_interesting_query(content);
  return false;
}

unsigned int afl_custom_fuzz_count(SquirrelMutator *mutator,
                                   const unsigned char *buf, size_t buf_size) {
  /*
  梳理count函数的逻辑
  首先connt函数将作为变异器选择站使用
  根据select成员变量的1 0 区分使用哪个变异器
  （0 ： zrcl ,  1 ： squirrel）
  初始判断标准，只要zrcl变异器有新的测试用例，就使用zrcl变异器
  若zrcl没有新的测试用例则使用squirrel变异器

  当一轮的变异结束后——即当上次的count返回值自减到0时，一轮结束开始调用count函数
  此时需要再次进行初始判断标准。

  当初始判断结束后，若判断采用zrcl，则返回1，且select = false
  若判断采用squirrel，则返回squirrel的原方法的返回值，且select = true
  */

  //开始判断是否采用zrcl变异器，即zrcl变异器是否具有新的测试用例
  mutator->select = !(mutator->zrcl_mutator.zrcl_is_have_new_in());
  //若有新的测试用例返回true 否则返回false
  if(mutator->select)
  {
    //若select为true，则采用squirrel变异器
    std::string sql((const char *)buf, buf_size);
    return mutator->database->mutate(sql);
  }
  //若select为false，则采用zrcl变异器
  return 1;
}

size_t afl_custom_fuzz(SquirrelMutator *mutator, uint8_t *buf, size_t buf_size,
                       u8 **out_buf, uint8_t *add_buf,
                       size_t add_buf_size,  // add_buf can be NULL
                       size_t max_size) {
  //当进入了fuzz后，开始判断使用的是哪种方法
  if (mutator->select)
  {
    //若select为true，则采用squirrel
    DataBase *db = mutator->database;
    assert(db->has_mutated_test_cases());
    mutator->current_input = db->get_next_mutated_query();
    *out_buf = (u8 *)mutator->current_input.c_str();
    return mutator->current_input.size();
  }
  else
  {
    //若select为false，则采用zrcl
    char LLM_in_path[100] = {0};  // 确保路径缓冲区足够大，并且初始化为0
    char file_name[50] = {0};     // 初始化文件名缓冲区

    // 拼接文件名并格式化路径
    snprintf(file_name, sizeof(file_name), "LLM_G_%d.txt", mutator->zrcl_mutator.fuzz_next);  // 使用 snprintf 格式化文件名
    snprintf(LLM_in_path, sizeof(LLM_in_path), "%s%s", mutator->zrcl_mutator.LLM_in_dir, file_name);  // 拼接完整路径

    //得到路径后，开始读取文件
		FILE* file = fopen(LLM_in_path, "r");

		if (file == NULL) {
			//此时若无法打开文件则表示LLM生成速度慢于测试速度，返回0，跳过本次变异,则只使用SQUIRREL
			return 0;
		}

		//获取文件大小
		fseek(file, 0, SEEK_END);
		size_t file_size = ftell(file);
		rewind(file);
		
		// 读取文件内容到缓冲区out_buf中

		*out_buf = (unsigned char*)malloc(file_size);
		size_t bytes_read = fread(*out_buf, 1, file_size, file);

		// 关闭文件
		fclose(file);
    mutator->zrcl_mutator.fuzz_next++;
    mutator->zrcl_mutator.fuzz_now++;
		// 返回读取的字节数
		return bytes_read;
  }
  
}
}
